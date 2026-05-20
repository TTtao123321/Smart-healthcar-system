# ============================================
# Stage 1: 使用 Maven 编译打包
# ============================================
FROM maven:3.8-openjdk-15 AS build
WORKDIR /app

# 先复制 POM 文件，利用 Docker 缓存加速依赖下载
COPY pom.xml ./
COPY common/pom.xml common/pom.xml
COPY hospital_hms_api/pom.xml hospital_hms_api/pom.xml
RUN mvn dependency:go-offline -B || true

# 复制源码并编译
COPY common common
COPY hospital_hms_api hospital_hms_api
RUN mvn clean package -DskipTests -B

# ============================================
# Stage 2: 精简 JRE 运行
# ============================================
FROM openjdk:15-jre-slim
WORKDIR /app
COPY --from=build /app/hospital_hms_api/target/hospital_hms_api-*.jar app.jar
EXPOSE 9091
ENTRYPOINT ["java", "-jar", "app.jar"]