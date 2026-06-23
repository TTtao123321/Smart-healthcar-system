# ============================================
# Stage 1: 使用 Node 编译 Vue 项目
# ============================================
FROM node:16-alpine AS build
WORKDIR /app

# 安装依赖
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并构建
COPY vite.config.js ./
COPY index.html ./
COPY src src
COPY static static
COPY favicon.png ./

RUN npm run build

# ============================================
# Stage 2: Nginx 运行
# ============================================
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html/hms-vue
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80