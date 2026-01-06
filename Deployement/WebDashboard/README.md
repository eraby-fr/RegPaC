# WebDashboard Docker Image

Dockerfile pour créer une image Docker légère du WebDashboard RegPaC, compatible Raspberry Pi 3B (ARMv7).

## Caractéristiques

- **Base**: `python:3.11-slim-bookworm` (layers mutualisés avec le backend)
- **Build**: Node.js 18.x LTS pour compiler l'application Vite/React
- **Runtime**: Serveur HTTP Python simple et léger
- **Compatible**: Raspberry Pi 3B (ARM32v7) et autres architectures
- **Port**: 80

## Build de l'image

Depuis la racine du projet RegPaC :

```bash
docker build -f Deployement/WebDashboard/dockerfile -t regpac-webdashboard:latest .
```

## Lancement du container

```bash
docker run -d \
  --name regpac-web \
  -p 80:80 \
  --restart unless-stopped \
  regpac-webdashboard:latest
```

Le dashboard sera accessible sur `http://localhost:80`

## Build multi-architecture (optionnel)

Pour builder pour Raspberry Pi depuis une autre architecture :

```bash
docker buildx build \
  --platform linux/arm/v7 \
  -f Deployement/WebDashboard/dockerfile \
  -t regpac-webdashboard:latest \
  .
```

## Notes

- L'application est buildée pendant la création de l'image
- Les fichiers statiques sont servis depuis `/app/dist`
- Le serveur Python inclut des headers no-cache pour éviter les problèmes de mise à jour
- Les `node_modules` sont supprimés après le build pour réduire la taille de l'image
