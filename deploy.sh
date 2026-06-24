#!/usr/bin/env bash
# ============================================================
#  deploy.sh — Script de despliegue para GESPRO-V1
#  Uso:  ./deploy.sh [OPCION]
#
#  Opciones:
#    up        Construir imágenes y levantar contenedores (por defecto)
#    down      Detener y eliminar contenedores
#    restart   Reiniciar todos los servicios
#    logs      Ver logs en tiempo real
#    status    Mostrar estado de los contenedores
#    migrate   Ejecutar migraciones de Django
#    shell     Abrir shell de Django dentro del contenedor
#    backup    Respaldar la base de datos
#    rebuild   Reconstruir imágenes desde cero (sin caché)
# ============================================================

set -euo pipefail

# ─── Colores para la salida ──────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # Sin color

# ─── Variables de configuración ──────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
ENV_FILE="${PROJECT_DIR}/.env"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ─── Funciones auxiliares ────────────────────────────────────

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo -e "${BOLD}${CYAN}"
    echo "╔══════════════════════════════════════════╗"
    echo "║        🚀 GESPRO-V1 — Deploy Tool       ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ─── Validaciones previas ────────────────────────────────────

check_dependencies() {
    log_info "Verificando dependencias..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado. Instálalo desde https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado."
        exit 1
    fi

    log_success "Docker y Docker Compose están disponibles."
}

# Determinar el comando de Docker Compose (v1 o v2)
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

check_env_file() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_error "No se encontró el archivo .env en ${ENV_FILE}"
        log_warn "Crea uno basándote en el README.md del proyecto."
        echo ""
        echo "  Variables requeridas:"
        echo "    GROUP, PROJECT, BACKEND_PORT"
        echo "    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD"
        echo "    DB_NAME, DB_USER, DB_PASSWORD"
        echo ""
        exit 1
    fi

    # Cargar variables del .env
    set -a
    source "${ENV_FILE}"
    set +a

    # Validar variables críticas para docker-compose.yml
    local required_vars=("BACKEND_PORT")
    local missing=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing+=("$var")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Faltan variables en .env: ${missing[*]}"
        exit 1
    fi

    log_success "Archivo .env cargado correctamente."
}

# ─── Comandos principales ────────────────────────────────────

do_up() {
    log_info "Construyendo imágenes y levantando contenedores..."
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

    echo ""
    log_success "¡Despliegue completado!"
    echo ""

    # Esperar a que los contenedores estén saludables
    log_info "Esperando a que los servicios estén listos..."
    sleep 5

    do_status

    local port="${BACKEND_PORT:-3003}"
    echo ""
    echo -e "  ${BOLD}🌐 La aplicación está disponible en:${NC}"
    echo -e "     ${GREEN}http://localhost:${port}${NC}"
    echo ""
}

do_down() {
    log_info "Deteniendo y eliminando contenedores..."
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down

    log_success "Contenedores detenidos y eliminados."
}

do_restart() {
    log_info "Reiniciando servicios..."
    do_down
    do_up
}

do_logs() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    log_info "Mostrando logs (Ctrl+C para salir)..."
    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs -f --tail=100
}

do_status() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    log_info "Estado de los contenedores:"
    echo ""
    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
}

do_migrate() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    log_info "Ejecutando migraciones de Django..."

    local backend_container
    backend_container=$(${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q backend)

    if [ -z "${backend_container}" ]; then
        log_error "El contenedor del backend no está corriendo. Ejecuta './deploy.sh up' primero."
        exit 1
    fi

    docker exec -it "${backend_container}" python backend/manage.py migrate

    log_success "Migraciones aplicadas correctamente."
}

do_shell() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    log_info "Abriendo Django shell..."

    local backend_container
    backend_container=$(${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q backend)

    if [ -z "${backend_container}" ]; then
        log_error "El contenedor del backend no está corriendo. Ejecuta './deploy.sh up' primero."
        exit 1
    fi

    docker exec -it "${backend_container}" python backend/manage.py shell
}

do_backup() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    mkdir -p "${BACKUP_DIR}"

    log_info "Creando respaldo de la base de datos..."

    local db_container
    db_container=$(${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q database)

    if [ -z "${db_container}" ]; then
        log_error "El contenedor de la base de datos no está corriendo."
        exit 1
    fi

    local backup_file="${BACKUP_DIR}/gespro_backup_${TIMESTAMP}.sql"

    docker exec "${db_container}" pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        > "${backup_file}"

    if [ -f "${backup_file}" ] && [ -s "${backup_file}" ]; then
        log_success "Respaldo creado: ${backup_file}"
        log_info "Tamaño: $(du -h "${backup_file}" | cut -f1)"
    else
        log_error "Error al crear el respaldo."
        rm -f "${backup_file}"
        exit 1
    fi
}

do_rebuild() {
    log_info "Reconstruyendo imágenes sin caché..."
    local compose_cmd
    compose_cmd=$(get_compose_cmd)

    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --no-cache
    ${compose_cmd} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d

    log_success "Reconstrucción completada."
    do_status
}

show_help() {
    echo -e "${BOLD}Uso:${NC} ./deploy.sh [OPCION]"
    echo ""
    echo "Opciones disponibles:"
    echo -e "  ${GREEN}up${NC}        Construir y levantar contenedores (por defecto)"
    echo -e "  ${GREEN}down${NC}      Detener y eliminar contenedores"
    echo -e "  ${GREEN}restart${NC}   Reiniciar todos los servicios"
    echo -e "  ${GREEN}logs${NC}      Ver logs en tiempo real"
    echo -e "  ${GREEN}status${NC}    Mostrar estado de los contenedores"
    echo -e "  ${GREEN}migrate${NC}   Ejecutar migraciones de Django"
    echo -e "  ${GREEN}shell${NC}     Abrir Django shell en el contenedor"
    echo -e "  ${GREEN}backup${NC}    Respaldar la base de datos (PostgreSQL)"
    echo -e "  ${GREEN}rebuild${NC}   Reconstruir imágenes sin caché"
    echo -e "  ${GREEN}help${NC}      Mostrar esta ayuda"
    echo ""
}

# ─── Punto de entrada ────────────────────────────────────────

main() {
    print_banner
    check_dependencies
    check_env_file

    local action="${1:-up}"

    case "${action}" in
        up)       do_up       ;;
        down)     do_down     ;;
        restart)  do_restart  ;;
        logs)     do_logs     ;;
        status)   do_status   ;;
        migrate)  do_migrate  ;;
        shell)    do_shell    ;;
        backup)   do_backup   ;;
        rebuild)  do_rebuild  ;;
        help|-h|--help) show_help ;;
        *)
            log_error "Opción desconocida: ${action}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
