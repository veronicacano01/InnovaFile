import bcrypt

from datetime import (
    datetime,
    timezone,
    timedelta
)

from pymongo.errors import DuplicateKeyError

from repositories import auth_repository


# ============================================================
# CONFIGURACIÓN
# ============================================================

MAX_FAILED_ATTEMPTS = 3
LOCK_TIME_SECONDS = 30


# ============================================================
# EXCEPCIONES
# ============================================================

class AuthServiceError(Exception):
    pass


class InvalidCredentialsError(
    AuthServiceError
):
    pass


class AccountLockedError(
    AuthServiceError
):

    def __init__(
        self,
        message,
        remaining_seconds=0
    ):
        super().__init__(
            message
        )

        self.remaining_seconds = (
            remaining_seconds
        )


class InvalidRegistrationError(
    AuthServiceError
):
    pass


class DuplicateUserError(
    AuthServiceError
):
    pass


# ============================================================
# CONTRASEÑAS
# ============================================================

def verify_password(
    plain,
    hashed
):

    if not hashed:
        return False

    hashed_value = (
        hashed.encode("utf-8")
        if isinstance(
            hashed,
            str
        )
        else hashed
    )

    # Compatibilidad con bcrypt de Laravel
    if hashed_value.startswith(
        b"$2y$"
    ):
        hashed_value = (
            b"$2b$"
            + hashed_value[4:]
        )

    try:

        return bcrypt.checkpw(
            plain.encode(
                "utf-8"
            ),
            hashed_value
        )

    except Exception:

        return False


def hash_password(
    password
):

    return bcrypt.hashpw(
        password.encode(
            "utf-8"
        ),
        bcrypt.gensalt()
    ).decode(
        "utf-8"
    )


def validate_password(
    password
):

    if not password:

        raise InvalidRegistrationError(
            "La contraseña es obligatoria."
        )

    if len(password) < 8:

        raise InvalidRegistrationError(
            "La contraseña debe tener mínimo 8 caracteres."
        )

    if not any(
        character.isupper()
        for character in password
    ):

        raise InvalidRegistrationError(
            "La contraseña debe incluir al menos una letra mayúscula."
        )

    if not any(
        character.islower()
        for character in password
    ):

        raise InvalidRegistrationError(
            "La contraseña debe incluir al menos una letra minúscula."
        )

    if not any(
        character.isdigit()
        for character in password
    ):

        raise InvalidRegistrationError(
            "La contraseña debe incluir al menos un número."
        )


# ============================================================
# BLOQUEO
# ============================================================

def get_lock_seconds_remaining(
    user
):

    locked_until = user.get(
        "locked_until"
    )

    if not locked_until:
        return 0

    now = datetime.now(
        timezone.utc
    )

    if locked_until.tzinfo is None:
        locked_until = (
            locked_until.replace(
                tzinfo=timezone.utc
            )
        )

    if locked_until <= now:
        return 0

    return max(
        int(
            (
                locked_until
                - now
            ).total_seconds()
        ),
        0
    )


def clear_expired_lock(
    user
):

    remaining_seconds = (
        get_lock_seconds_remaining(
            user
        )
    )

    if remaining_seconds > 0:
        return

    attempts = user.get(
        "failed_login_attempts",
        0
    )

    locked_until = user.get(
        "locked_until"
    )

    if (
        attempts > 0
        or locked_until is not None
    ):

        now = datetime.now(
            timezone.utc
        )

        auth_repository.update_login_security(
            user["_id"],
            failed_login_attempts=0,
            locked_until=None,
            updated_at=now
        )

        user[
            "failed_login_attempts"
        ] = 0

        user[
            "locked_until"
        ] = None


def register_failed_attempt(
    user
):

    attempts = (
        user.get(
            "failed_login_attempts",
            0
        )
        + 1
    )

    now = datetime.now(
        timezone.utc
    )

    locked_until = None

    if attempts >= MAX_FAILED_ATTEMPTS:

        locked_until = (
            now
            + timedelta(
                seconds=LOCK_TIME_SECONDS
            )
        )

    auth_repository.update_login_security(
        user["_id"],
        failed_login_attempts=attempts,
        locked_until=locked_until,
        updated_at=now
    )

    return {
        "attempts": attempts,
        "locked": (
            locked_until is not None
        ),
        "locked_until": locked_until
    }


def reset_login_security(
    user
):

    now = datetime.now(
        timezone.utc
    )

    auth_repository.update_login_security(
        user["_id"],
        failed_login_attempts=0,
        locked_until=None,
        last_login_at=now,
        updated_at=now
    )


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    email,
    password
):

    email = (
        email or ""
    ).strip().lower()

    password = (
        password or ""
    )

    if not email or not password:

        raise InvalidCredentialsError(
            "Ingresa correo y contraseña."
        )

    user = (
        auth_repository
        .get_user_by_email(
            email
        )
    )

    # Mensaje genérico para no revelar
    # si el correo existe.
    if not user:

        raise InvalidCredentialsError(
            "Correo o contraseña incorrectos."
        )

    remaining_seconds = (
        get_lock_seconds_remaining(
            user
        )
    )

    if remaining_seconds > 0:

        raise AccountLockedError(
            (
                "Tu cuenta está bloqueada temporalmente. "
                f"Intenta nuevamente en "
                f"{remaining_seconds} segundos."
            ),
            remaining_seconds
        )

    clear_expired_lock(
        user
    )

    if not verify_password(
        password,
        user.get(
            "password"
        )
    ):

        failed_result = (
            register_failed_attempt(
                user
            )
        )

        if failed_result[
            "locked"
        ]:

            raise AccountLockedError(
                (
                    "Demasiados intentos fallidos. "
                    f"La cuenta se bloqueó durante "
                    f"{LOCK_TIME_SECONDS} segundos."
                ),
                LOCK_TIME_SECONDS
            )

        remaining_attempts = (
            MAX_FAILED_ATTEMPTS
            - failed_result[
                "attempts"
            ]
        )

        error = InvalidCredentialsError(
            (
                "Correo o contraseña incorrectos. "
                f"Te quedan "
                f"{remaining_attempts} intento(s)."
            )
        )

        error.attempts = (
            failed_result[
                "attempts"
            ]
        )

        error.user = user

        raise error

    reset_login_security(
        user
    )

    return user


# ============================================================
# REGISTRO
# ============================================================

def register_user(
    name,
    last_name,
    email,
    password,
    role_id=None,
):
    name = (name or "").strip()
    last_name = (last_name or "").strip()
    email = (email or "").strip().lower()

    if not all([name, last_name, email, password]):
        raise InvalidRegistrationError("Completa todos los campos.")

    if len(name) > 100:
        raise InvalidRegistrationError("El nombre es demasiado largo.")

    if len(last_name) > 100:
        raise InvalidRegistrationError("El apellido es demasiado largo.")

    if "@" not in email or "." not in email:
        raise InvalidRegistrationError("Ingresa un correo válido.")

    validate_password(password)

    # --------------------------------------------------------
    # VALIDAR ROL
    # --------------------------------------------------------
    # Si se especifica un rol, debe existir y NO ser Administrador.
    # Si no se especifica, se usa "Empleado" o el primer rol no-admin.

    role = None

    if role_id:
        try:
            from bson import ObjectId
            role = auth_repository.get_role_by_id(ObjectId(role_id))
        except Exception:
            role = None

        if not role:
            raise InvalidRegistrationError("El rol seleccionado no existe.")

    else:
        role = auth_repository.get_role_by_name("Empleado")
        if not role:
            all_roles = auth_repository.get_all_roles()
            role = next(
                (r for r in all_roles if r.get("name") != "Administrador"),
                None,
            )

    if not role:
        raise InvalidRegistrationError(
            "No hay roles disponibles. Contacta al administrador."
        )

    # Bloqueo explícito de Administrador
    if role.get("name") == "Administrador":
        raise InvalidRegistrationError(
            "No puedes registrarte con el rol Administrador."
        )

    now = datetime.now(timezone.utc)

    user_data = {
        "name": name,
        "last_name": last_name,
        "email": email,
        "password": hash_password(password),
        "role_id": role["_id"],
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = auth_repository.create_user(user_data)
    except DuplicateKeyError:
        raise DuplicateUserError("Ese correo ya está registrado.")

    user_data["_id"] = result.inserted_id
    return user_data