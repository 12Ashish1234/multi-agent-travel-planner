FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

ENV NEXT_TELEMETRY_DISABLED=1

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]