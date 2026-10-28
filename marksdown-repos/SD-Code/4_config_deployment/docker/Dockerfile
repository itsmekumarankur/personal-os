# 34. DOCKERFILE for a Spring Boot microservice (multi-stage build)
# NOT built or run by the author (no Docker or Maven Central access in the authoring sandbox).
#
# Build : docker build -f docker/Dockerfile -t payment-service:1.0.0 .
# Run   : docker run -p 8080:8080 -e SPRING_PROFILES_ACTIVE=prod -e APP_DB_PASSWORD=secret payment-service:1.0.0

# ---------- Stage 1: BUILD (has JDK + Maven, is thrown away afterwards) ----------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
RUN mvn -q dependency:go-offline          # cached layer: only re-runs when pom.xml changes
COPY src ./src
RUN mvn -q package -DskipTests

# ---------- Stage 2: RUN (small JRE-only image, no compiler, no Maven, no source) ----------
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S app && adduser -S app -G app   # never run as root
USER app
WORKDIR /app
COPY --from=build /workspace/target/*.jar app.jar

EXPOSE 8080
# container-aware JVM sizing: use 75% of the memory limit the platform gives the container
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75"
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD wget -qO- http://localhost:8080/actuator/health/liveness || exit 1
# exec form: java is PID 1 and receives SIGTERM, so graceful shutdown works
ENTRYPOINT ["java", "-jar", "app.jar"]
# ================================================================
# SPRING BOOT MICROSERVICE - MULTI-STAGE DOCKER BUILD
# ================================================================
#
#                   DEVELOPER / SOURCE CODE
#                            |
#                            v
#                  +--------------------+
#                  | pom.xml            |
#                  | src/               |
#                  | Java source code   |
#                  +---------+----------+
#                            |
#                            v
# ================================================================
# STAGE 1: BUILD
# ================================================================
#
#   Base image: maven:3.9-eclipse-temurin-21
#
#   +------------------------------------------+
#   | BUILD IMAGE                              |
#   |                                          |
#   | JDK 21 + Maven                           |
#   |                                          |
#   | 1. Set WORKDIR /workspace                |
#   | 2. Copy pom.xml                          |
#   | 3. Download/cache dependencies           |
#   | 4. Copy src/                             |
#   | 5. Run mvn package -DskipTests           |
#   |                                          |
#   | Output: target/*.jar                     |
#   +---------------------+--------------------+
#                         |
#                         | COPY --from=build
#                         | Only the generated JAR
#                         v
# ================================================================
# STAGE 2: RUNTIME
# ================================================================
#
#   Base image: eclipse-temurin:21-jre-alpine
#
#   +------------------------------------------+
#   | RUNTIME IMAGE                            |
#   |                                          |
#   | Small JRE-only base image                |
#   |                                          |
#   | - Create non-root user: app              |
#   | - Switch to USER app                     |
#   | - Set WORKDIR /app                       |
#   | - Copy application JAR as app.jar        |
#   | - Configure JVM memory sizing            |
#   | - Configure health check                 |
#   | - Start Java application                 |
#   |                                          |
#   | No Maven, JDK compiler, or source code   |
#   +---------------------+--------------------+
#                         |
#                         v
# ================================================================
# CONTAINER STARTUP
# ================================================================
#
#   docker run -p 8080:8080 ...
#                 |
#                 v
#   +------------------------------------------+
#   | Docker Container                         |
#   |                                          |
#   | ENTRYPOINT: java -jar app.jar            |
#   |                                          |
#   | Spring Boot application                  |
#   |           |                              |
#   |           v                              |
#   | HTTP server listens on port 8080         |
#   |           |                              |
#   |           v                              |
#   | /actuator/health/liveness                |
#   |           |                              |
#   |           v                              |
#   | Docker HEALTHCHECK                       |
#   +---------------------+--------------------+
#                         |
#                         v
#                Application requests
#                from clients / services
#
# ================================================================
# REQUEST FLOW
# ================================================================
#
#   Client
#     |
#     | HTTP :8080
#     v
#   Docker host port 8080
#     |
#     | -p 8080:8080
#     v
#   Container port 8080
#     |
#     v
#   Spring Boot application
#     |
#     v
#   Business logic / database
#
# ================================================================
# KEY BENEFITS
# ================================================================
#
# 1. Smaller runtime image: build tools are excluded.
# 2. Faster rebuilds: dependency layer can be cached.
# 3. Better security: application runs as non-root user.
# 4. Memory awareness: JVM sizes itself relative to container limit.
# 5. Health monitoring: Docker periodically checks liveness.
# 6. Graceful shutdown: exec-form ENTRYPOINT lets Java receive signals.
#
# ================================================================