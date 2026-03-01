# Stage 1: Build React app
# Build context MUST be repo root (render.yaml: dockerContext: .). If you see "package.json not found", set dockerContext to . in Render.
FROM node:20-alpine AS builder

WORKDIR /app

# Inject API URL at build time
ARG VITE_API_URL=https://escape-room-telegram-api.onrender.com
ARG VITE_BASE_PATH=/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# Copy package files (paths relative to frontend/ when context is repo root)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy full frontend directory
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]