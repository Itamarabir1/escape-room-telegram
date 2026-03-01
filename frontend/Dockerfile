# Stage 1: Build React app
# Build context must be repo root (e.g. render.yaml: dockerContext: .) so COPY frontend/... paths resolve.
FROM node:20-alpine AS builder

WORKDIR /app

# הזרקת ה-URL של ה-API
ARG VITE_API_URL=https://escape-room-telegram-api.onrender.com
ARG VITE_BASE_PATH=/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# תיקון הנתיבים - הוספת frontend/
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# העתקת כל תוכן תיקיית הפרונטנד
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
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
    } \
  }' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]