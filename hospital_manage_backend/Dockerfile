# ============================================
# Stage 1: 使用 Maven 编译打包(JDK 17,与 pom.xml java.version 对齐;ARM64 原生支持)
# ============================================
ARG REGISTRY_PREFIX=docker.io/library
FROM ${REGISTRY_PREFIX}/maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

# 可选:配置 Maven 镜像加速依赖下载(默认空,使用 Maven 中央仓库)
# 在 docker compose / build 时传入 --build-arg MAVEN_MIRROR_URL=https://maven.aliyun.com/repository/public 启用
ARG MAVEN_MIRROR_URL=""
COPY maven-settings.xml /tmp/maven-settings.xml
RUN mkdir -p /root/.m2 && if [ -n "$MAVEN_MIRROR_URL" ]; then \
        sed "s|__MAVEN_MIRROR_URL__|${MAVEN_MIRROR_URL}|g" /tmp/maven-settings.xml > /root/.m2/settings.xml; \
    fi

# 先复制 POM 文件,利用 Docker 缓存加速依赖下载
COPY pom.xml ./
COPY common/pom.xml common/pom.xml
COPY hospital_hms_api/pom.xml hospital_hms_api/pom.xml
RUN mvn dependency:go-offline -B || true

# 复制源码并编译
COPY common common
COPY hospital_hms_api hospital_hms_api
RUN mvn clean install -Dmaven.test.skip=true -B

# ============================================
# Stage 2: 精简 JRE 运行(eclipse-temurin 17,ARM64 原生)
# ============================================
FROM ${REGISTRY_PREFIX}/eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /app/hospital_hms_api/target/hospital_hms_api-*.jar app.jar
EXPOSE 9091
ENTRYPOINT ["java", "-jar", "app.jar"]
