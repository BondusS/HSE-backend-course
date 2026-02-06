from asyncpg.pool import Pool

class UserRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    # При необходимости сюда можно добавить методы для управления пользователями
    # например, create_user, get_user_by_id и т.д.
    pass
