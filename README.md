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
├── assets/                 # Sprites y audio usados por la demo arcade
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
- Demo arcade: http://localhost:9004/demo

## Crear tablas manualmente

Si necesitas crear las tablas sin levantar la API, ejecuta:

```bash
python scripts/create_tables.py
```

El script usa los modelos de `app/db/models.py`, la conexión configurada por `.env` y también asegura los roles base `player` y `moderator`.

## Demo arcade

La ruta `/demo` sirve una web simple estilo arcade para probar el flujo completo de gamificación sin depender de otro frontend.

Acciones disponibles:

- Ingresar un nombre; la demo genera y recuerda un UUID interno para ese nombre.
- Elegir un personaje desde los sprites de `assets/`.
- Mover el personaje con flechas, WASD o controles táctiles.
- Recolectar cristales para ganar puntos reales con `POST /api/v1/users/{user_id}/points/auto`.
- Ver puntos y coins en el HUD, con actualizaciones por WebSocket en `/api/v1/ws/{user_id}` cuando Redis está activo.
- Convertir puntos a coins con `POST /api/v1/users/me/convert` usando el header `x-user-id`.
- Ver un ranking de coins respaldado por Redis con jugadores conectados recientemente.

Rutas auxiliares de la demo:

- `POST /api/v1/demo/players/connect`: registra `display_name`, UUID interno y balance actual en Redis.
- `POST /api/v1/demo/players/heartbeat`: mantiene la presencia del jugador con TTL corto.
- `GET /api/v1/demo/leaderboard`: devuelve el ranking de coins ordenado de mayor a menor.

Para probarla:

1. Levantar el servicio con `docker compose up -d --build`.
2. Abrir http://localhost:9004/demo.
3. Ingresar un nombre y presionar **Conectar jugador**.
4. Iniciar la partida, recolectar cristales y convertir puntos cuando haya saldo suficiente.

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

Puerto por defecto **9004**. El `Dockerfile` no copia archivos `.env`; las variables se inyectan por entorno para que la misma imagen funcione en local, Docker Compose y Railway.

## Railway

Railway despliega este proyecto desde el `Dockerfile`. Para producción, crea en Railway un servicio para la API y agrega servicios gestionados de PostgreSQL y Redis.

Variables recomendadas en el servicio de la API:

- `PORT`: Railway lo inyecta automáticamente.
- `DATABASE_URL`: provista por el plugin/servicio PostgreSQL de Railway.
- `REDIS_URL`: provista por el plugin/servicio Redis de Railway.
- `POINTS_TO_COINS_RATE`: opcional, default `100`.
- `DEBUG`: opcional, recomendado `false`.

La app acepta `DATABASE_URL` directamente. Si no existe, usa las variables `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`.

Para probar localmente con el mismo estilo de variables externas:

```bash
DATABASE_URL="postgresql://user:password@host:5432/db" \
REDIS_URL="redis://host:6379/0" \
docker compose -f docker-compose.railway.yml up --build
```

## Variables de entorno

Ver `envs/.env.example`. Principales: `DATABASE_URL` o `POSTGRES_HOST`/`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`, `REDIS_URL` y `POINTS_TO_COINS_RATE` (tasa de conversión por defecto, default 100).
