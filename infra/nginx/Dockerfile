FROM nginx:1.27-alpine

# Install curl for in-container debugging (kept minimal)
RUN apk add --no-cache curl

COPY default.conf /etc/nginx/conf.d/default.conf
