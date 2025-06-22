'''This script analyzes GitHub commit messages to evaluate candidates' expertise:

1. Loads user data from a CSV file and standardizes job role names.  
2. Filters relevant roles (Web Developer, Java Developer) for analysis.   
3. Checks commit history for each user by reading corresponding commit files.   
4. Processes commit messages using TF-IDF scoring based on predefined keywords for each job role.   
5. Computes a commit score reflecting the relevance of a user's commits to their job role.   
6. Logs the processing steps and handles errors during TF-IDF computation.   
7. Updates the dataset with computed commit scores and additional feature columns.   
8. Saves the processed data to a new CSV file for further use.'''

import os
import pandas as pd
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer

class CommitAnalyzer:
    ROLE_KEYWORDS = {
        "Data science" : ["machine learning", "deep learning", "neural networks", "convolutional neural networks", "recurrent neural networks", "transformers", 
            "attention mechanism", "graph neural networks", "self-supervised learning", "semi-supervised learning", "meta-learning", "federated learning",
            "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "lightgbm", "catboost", "fastai", "pandas", "numpy", "scipy", 
            "matplotlib", "seaborn", "plotly", "bokeh", "altair", "dash", "holoviews", "jupyter", "google colab", "kaggle notebooks", "dvc", 
            "mlflow", "tensorboard", "optuna", "hyperopt", "bayesian optimization", "cross-validation", "stratified sampling", "time series cross-validation",
            "model ensembling", "stacking", "blending", "boosting", "bagging", "classification", "regression", "clustering", "anomaly detection", 
            "unsupervised learning", "semi-supervised learning", "reinforcement learning", "q-learning", "policy gradients", "actor-critic", 
            "markov decision process", "contextual bandits", "hadoop", "spark", "hive", "hdfs", "kafka", "flink", "beam", "bigquery", "redshift",
            "athena", "databricks", "aws sagemaker", "azure ml", "gcp ai platform", "vertex ai", "snowflake", "databricks delta lake", "dremio", 
            "data version control", "git-lfs", "elasticsearch", "opensearch", "vector similarity search", "pinecone", "chromadb", "milvus", 
            "natural language processing", "bert", "roberta", "gpt-3", "gpt-4", "t5", "bloom", "llama", "falcon", "text summarization", "text classification", 
            "sentiment analysis", "topic modeling", "lda", "hdp", "word2vec", "doc2vec", "fasttext", "transformer encoder-decoder", 
            "zero-shot learning", "few-shot learning", "contrastive learning", "prompt engineering", "data pipelines", "airflow", "dagster", "prefect", 
            "ci/cd pipelines", "jenkins", "gitlab ci", "circleci", "continuous deployment", "mlops", "kubeflow pipelines", "tfx", "ml model registry", 
            "model explainability", "shap", "lime", "explainable ai", "fairness metrics", "responsible ai", "differential privacy", "data privacy", 
            "gdpr compliance", "data anonymization", "k-anonymity", "differential privacy", "blockchain analytics", "graph databases", "neo4j", 
            "knowledge graphs", "ontologies", "semantic search", "embedding techniques", "contextual embeddings", "vector search"
        ],
        "Web Developer": [
            "html5", "css3", "sass", "less", "stylus", "postcss", "javascript", "typescript", "react", "vue", "angular", "svelte", "ember", 
            "nextjs", "nuxtjs", "astro", "remix", "gatsby", "eleventy", "hugo", "nodejs", "deno", "bun", "express", "nestjs", "koa", "fastify", 
            "graphql", "apollo server", "hasura", "rest api", "grpc", "websocket", "socket.io", "signalr", "webpack", "rollup", "esbuild", 
            "vite", "parcel", "babel", "swc", "jest", "cypress", "playwright", "mocha", "chai", "ava", "testing-library", "enzyme", "msw", 
            "storybook", "chromatic", "web components", "shadow dom", "custom elements", "pwa", "spa", "ssr", "csr", "isr", "swr", "hydration", 
            "server components", "seo", "lighthouse", "core web vitals", "accessibility", "aria roles", "semantic html", "responsive design", 
            "mobile-first", "adaptive design", "css grid", "flexbox", "tailwindcss", "bootstrap", "material-ui", "ant design", "chakra ui", "foundation", 
            "redux", "zustand", "mobx", "recoil", "context api", "react query", "swr", "apollo client", "axios", "fetch api", "rest hooks", 
            "auth0", "firebase auth", "jwt", "oauth2", "openid connect", "saml", "cors", "csrf", "helmet", "rate limiting", "express-validator", 
            "docker", "kubernetes", "serverless functions", "aws lambda", "azure functions", "google cloud functions", "vercel", "netlify", "cloudflare pages", 
            "firebase", "supabase", "mongodb", "postgresql", "mysql", "cockroachdb", "planetScale", "redis", "memcached", "prisma", "typeorm", 
            "sequelize", "mongoose", "nginx", "caddy server", "pm2", "jenkins", "github actions", "gitlab ci", "circleci", "sonarqube", "eslint", 
            "prettier", "husky", "lint-staged", "webassembly", "rust", "go", "service workers", "indexeddb", "localstorage", "sessionstorage", "cookies", 
            "http/2", "http/3", "quic", "cdn", "cloudflare", "akamai", "fastly", "image optimization", "lazy loading", "code splitting", "tree shaking", 
            "module federation", "micro-frontends", "jamstack", "headless cms", "contentful", "strapi", "sanity", "payload cms", "keystone js", 
            "shopify", "woocommerce", "stripe", "paypal", "razorpay", "apple pay", "web analytics", "google tag manager", "hotjar", "fullstory", 
            "error tracking", "sentry", "rollbar", "new relic", "elastic apm", "logging", "winston", "morgan", "pino", "opentelemetry", "datadog"
        ],
        "Java Developer": [
            "java 8", "java 11", "java 17", "java 21", "project loom", "project valhalla", "project panama", "spring boot", "spring mvc", "spring cloud", 
            "spring security", "spring batch", "spring webflux", "reactive programming", "hibernate", "jpa", "jdbc", "r2dbc", "junit 5", "mockito", 
            "assertj", "testcontainers", "lombok", "maven", "gradle", "buildship", "restful api", "graphql", "grpc", "soap", "kafka", "rabbitmq", 
            "pulsar", "active mq", "quarkus", "micronaut", "vertx", "spring integration", "jakarta ee", "jsf", "servlet", "jax-rs", "jax-ws", "thymeleaf", 
            "freemarker", "swagger", "openapi", "oauth2", "jwt", "spring cloud gateway", "eureka", "hystrix", "zipkin", "sleuth", "resilience4j", 
            "docker", "kubernetes", "helm", "istio", "linkerd", "aws", "azure", "gcp", "oracle cloud", "oci", "oracle db", "mysql", "postgresql", 
            "mariadb", "mongodb", "cassandra", "neo4j", "dynamodb", "redis", "hazelcast", "ignite", "liquibase", "flyway", "jenkins", "github actions", 
            "gitlab ci", "circleci", "sonarqube", "checkstyle", "pmd", "spotbugs", "jacoco", "log4j2", "logback", "slf4j", "jvm tuning", "graalvm", 
            "substrate vm", "project reactor", "rxjava", "java concurrency", "fork-join framework", "completablefuture", "parallel streams", 
            "virtual threads", "structured concurrency", "nio", "aio", "serialization", "jackson", "gson", "protobuf", "avro", "thrift", "mapstruct", 
            "bean validation", "hibernate validator", "event sourcing", "cqrs", "domain-driven design", "hexagonal architecture", "clean architecture", 
            "monolithic architecture", "microkernel architecture", "event-driven architecture", "reactive architecture", "test-driven development", 
            "behavior-driven development", "contract testing", "mutation testing", "pact", "spring aop", "aspectj", "saga pattern", "circuit breaker", 
            "bulkhead", "rate limiter", "retry", "distributed tracing", "jaeger", "opentracing", "zipkin", "opentelemetry", "metrics", "micrometer"
        ]
    }

    ROLE_FILE_TYPES = {
        "Web Developer": [".html", ".css", ".js"],
        "Java Developer": [".java", ".xml", ".gradle"]
    }

    COMMIT_SCORE_COLUMN = "commit_score"
    LOG_FILE = "commit_processing_final.log"

    @staticmethod
    def log_message(message):
        
        with open(CommitAnalyzer.LOG_FILE, "a") as log:
            log.write(message + "\n")
        print(message)

    @staticmethod
    def calculate_tfidf_score(commit_messages, keywords):
        
        if not keywords:
            return [0] * len(commit_messages)

        tfidf_vectorizer = TfidfVectorizer(vocabulary=[kw.lower() for kw in keywords], lowercase=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(commit_messages)
        return tfidf_matrix.sum(axis=1)

    @staticmethod
    def normalize_job_role(role):
        
        role_lower = role.lower().strip()
        if "javascript" in role_lower or "java script" in role_lower or role_lower == "js":
            return "Web Developer"
        elif "java" in role_lower:
            return "Java Developer"
        elif "web" in role_lower:
            return "Web Developer"
        else:
            return role.title()

    def process_final_data(self, final_data_path, commit_files_dir):
        
        self.log_message("\nStarting commit analysis...")

        
        users_df = pd.read_csv(final_data_path)
        users_df["username"] = users_df["username"].str.strip()
        users_df["job role"] = users_df["job role"].apply(self.normalize_job_role)

        
        users_df = users_df[users_df["job role"].isin(["Web Developer", "Java Developer"])]

        if users_df.empty:
            self.log_message("No relevant users found! Exiting...")
            return

        if self.COMMIT_SCORE_COLUMN not in users_df.columns:
            users_df[self.COMMIT_SCORE_COLUMN] = 0.0

        users_df["feature_1"] = 0
        users_df["feature_2"] = 0
        users_df["feature_3"] = 0

        users_to_keep = []

        for index, row in users_df.iterrows():
            username = row["username"]
            job_role = row["job role"]

            commit_file = os.path.join(commit_files_dir, f"{username}_commit_details.csv")
            if not os.path.exists(commit_file):
                self.log_message(f"No commit file for {username} → Skipping...")
                continue

            self.log_message(f"Processing commit file for {username}")

            commits_df = pd.read_csv(commit_file)
            commits_df["commit_message"] = commits_df["commit_message"].fillna("").astype(str)

            if commits_df["commit_message"].str.strip().eq("").all():
                self.log_message(f"No valid commit messages for {username} → Skipping...")
                continue

            keywords = self.ROLE_KEYWORDS.get(job_role, [])
            try:
                scores = self.calculate_tfidf_score(commits_df["commit_message"].tolist(), keywords)
                users_df.at[index, self.COMMIT_SCORE_COLUMN] = scores.sum()
                self.log_message(f"Computed TF-IDF score for {username}: {scores.sum()}")
            except Exception as e:
                self.log_message(f"Error in TF-IDF computation for {username}: {str(e)}")
                continue

            users_to_keep.append(index)

        users_df = users_df.loc[users_to_keep]
        output_file = final_data_path.replace(".csv", "_final_updated.csv")
        users_df.to_csv(output_file, index=False)
        self.log_message(f"\nProcessing complete. Updated data saved to {output_file}")



final_data_path = "/home/ashwin_jayan/EXTRACT/final_data.csv"
commit_files_dir = "/home/ashwin_jayan/EXTRACT/combined_commit_message/"

analyzer = CommitAnalyzer()
analyzer.process_final_data(final_data_path, commit_files_dir)
