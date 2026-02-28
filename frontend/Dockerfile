# Stage 1: Build React app
FROM node:20-alpine AS builder

WORKDIR /app

# Build-time args (Vite bakes these into the bundle)
ARG VITE_API_URL
ARG VITE_BASE_PATH=/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev || npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Serve SPA: try file, then fallback to index.html for client-side routes
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
      try_files $uri $uri/ /index.html; \
    } \
    location /health { \
      access_log off; \
      return 200 "ok"; \
      add_header Content-Type text/plain; \
    } \
  }' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
