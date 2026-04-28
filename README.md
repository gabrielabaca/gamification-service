# Gamification Service

Microservicio FastAPI para gestionar la gamificación de la plataforma: points, coins, roles y auditoría de operaciones por usuario. Se integra con el `platform-portal-cc` como puente de autenticación — el portal valida el JWT y reenvía el `user_id` por header `x-user-id`.

## Estructura del proyecto

```
gamification-service/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py       # Settings con pydantic-settings
│   │   └── security.py     # Valida x-user-id y rol de gamificación
│   ├── db/
│   │   ├── session.py      # Engine async + get_db
│   │   ├── models.py       # Role, UserRole, UserBalance, CoinConfig, AuditLog
│   │   └── repository.py   # Repositorios por modelo
│   ├── schemas/
│   │   ├── points.py       # Schemas de users, roles y balance
│   │   └── coins.py        # Schemas de CoinConfig y AuditLog
│   ├── services/
│   │   ├── gamification.py # Lógica de negocio
│   │   └── notifier.py     # Pub/Sub Redis para tiempo real
│   ├── clients/
│   │   └── redis_client.py # Singleton Redis async
│   └── api/v1/
│       ├── points.py       # Endpoints de users
│       ├── coins.py        # CRUD CoinConfig
│       ├── roles.py        # Endpoints de roles
│       └── websocket.py    # WebSocket /ws/{user_id}
├── envs/
│   ├── .env.example        # Variables requeridas (sin valores)
│   └── .env.main           # Variables de producción
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Configuración

1. Copiar variables de entorno:
   ```bash
   cp envs/.env.example .env
   ```
2. Editar `.env` y configurar al menos:
   - `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   - `REDIS_URL`

## Ejecución local

```bash
docker compose up -d --build
```

- Docs: http://localhost:9004/docs
- Health: http://localhost:9004/health

## Seed del primer moderador

El sistema de roles es circular por diseño: solo un moderador puede asignar roles a otros usuarios. Como al inicio no existe ningún moderador, el primero debe insertarse manualmente en la BD una sola vez. A partir de ahí ese moderador puede asignar roles a todos los demás usuarios desde los endpoints normales.

```bash
docker exec gamification-postgres psql -U gamification_user -d gamification_db -c "
INSERT INTO user_roles (id, user_id, role_id, assigned_by, created_at, updated_at)
SELECT gen_random_uuid(), '<user-id>', id, '<user-id>', now(), now()
FROM roles WHERE name = 'moderator'
ON CONFLICT ON CONSTRAINT uq_user_roles_user_id DO NOTHING;"
```

## Docker

Puerto por defecto **9004**. El `Dockerfile` copia `envs/.env.main` a `/app/.env`.

## Variables de entorno

Ver `envs/.env.example`. Principales: `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `REDIS_URL` y `POINTS_TO_COINS_RATE` (tasa de conversión por defecto, default 100).
