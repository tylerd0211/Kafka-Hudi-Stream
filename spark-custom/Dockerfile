# spark-custom/Dockerfile
FROM bitnami/spark:3.3.0

USER root

# Install wget to download the Hudi JAR
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Download the Hudi JAR and place it in Spark's jars directory
RUN wget https://repo1.maven.org/maven2/org/apache/hudi/hudi-spark3.3-bundle_2.12/0.14.0/hudi-spark3.3-bundle_2.12-0.14.0.jar -P /opt/bitnami/spark/jars/

# Change back to non-root user
USER 1001

