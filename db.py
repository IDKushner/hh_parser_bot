import datetime
from SETTINGS import postgres_settings as p
from sqlalchemy import (
    ChunkedIteratorResult,
    Integer,
    CHAR,
    String,
    ForeignKey,
    Text,
    Boolean,
    DateTime,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.mutable import MutableList

engine = create_async_engine(
    url=f'postgresql+asyncpg://{p["user"]}:{p["password"]}@{p["host"]}:{p["port"]}/{p["db"]}',
    echo=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass

    @staticmethod
    async def start():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def shutdown():
        await engine.dispose()


class Experience(Base):
    __tablename__ = "experience_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    users: Mapped["User"] = relationship(back_populates="experience")


class Employer_Type(Base):
    __tablename__ = "employers_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)


async def get_employers_types(reverse: bool = False) -> dict:
    async with async_session() as session:
        employers_types: ChunkedIteratorResult[
            (Employer_Type.id, Employer_Type.name)
        ] = await session.execute(select(Employer_Type.id, Employer_Type.name))

        # Вид возвращаемого поля: 'Консалтинг' : 0
        if reverse:
            employers_types_as_dict = {
                employer_type[1]: employer_type[0]
                for employer_type in employers_types.all()
            }

        # Вид возвращаемого поля: 0 : 'Консалтинг'
        else:
            employers_types_as_dict = {
                employer_type[0]: employer_type[1]
                for employer_type in employers_types.all()
            }

        return employers_types_as_dict


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(CHAR(32), unique=False, nullable=False)
    experience_id: Mapped[int] = mapped_column(
        ForeignKey("experience_types.id"), nullable=False
    )
    experience: Mapped["Experience"] = relationship(back_populates="users")
    salary: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    area: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)), unique=False, nullable=False
    )
    desired_employer_type_names: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)), unique=False, nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, unique=False, nullable=False, default=False
    )

    async def add_or_update(self):
        async with async_session() as session:
            existing_user: ChunkedIteratorResult = await session.execute(
                select(User).where(User.telegram_id == self.telegram_id)
            )

            if not existing_user.scalar_one_or_none():
                session.add(self)

                await session.commit()

            else:
                await session.execute(
                    update(User)
                    .where(User.telegram_id == self.telegram_id)
                    .values(
                        telegram_id=self.telegram_id,
                        username=self.username,
                        experience_id=self.experience_id,
                        salary=self.salary,
                        tags=self.tags,
                        area=self.area,
                        desired_employer_type_names=self.desired_employer_type_names,
                    )
                )

                await session.commit()


async def check_if_user_exists(telegram_id: int) -> bool:
    async with async_session() as session:
        existing_user: ChunkedIteratorResult = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not existing_user.scalar_one_or_none():
            return False
        return True


async def get_user_by_id(user_id: int) -> User or None:
    async with async_session() as session:
        user: ChunkedIteratorResult[User] = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )

        return user.scalar_one_or_none()


async def enable_or_disable_admin(telegram_id: int, is_admin: bool):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_admin=is_admin)
        )

        await session.commit()


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hh_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=False, nullable=False)
    url: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    employer_name: Mapped[str] = mapped_column(String, unique=False, nullable=False)
    employer_type_id: Mapped[int] = mapped_column(
        ForeignKey("employers_types.id"), nullable=True
    )
    experience_id: Mapped[int] = mapped_column(
        ForeignKey("experience_types.id"), nullable=False
    )
    salary: Mapped[dict] = mapped_column(JSON, unique=False, nullable=True)
    address: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    metro_stations: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)), nullable=True
    )
    tags: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)), unique=False, nullable=False
    )
    is_sent: Mapped[bool] = mapped_column(
        Boolean, unique=False, nullable=False, default=False
    )
    from_admin: Mapped[bool] = mapped_column(
        Boolean, unique=False, nullable=False, default=False
    )
    description: Mapped[str] = mapped_column(Text, unique=False, nullable=False)

    async def add(self):
        async with async_session() as session:
            existing_vacancy: ChunkedIteratorResult[Vacancy] = await session.execute(
                select(Vacancy).where(Vacancy.hh_id == self.hh_id)
            )
            if not existing_vacancy.scalar_one_or_none():
                session.add(self)
                await session.commit()

    async def change_status(self):
        """Меняет is_sent отправленной вакансии на True"""
        async with async_session() as session:
            await session.execute(
                update(Vacancy).where(Vacancy.hh_id == self.hh_id).values(is_sent=True)
            )

            await session.commit()

    async def get_suitable_users(self) -> ChunkedIteratorResult[User]:
        """Выбирает из базы пользователей, подходящих под вакансию
        по тегам, опыту и зарплатным ожиданиям"""
        async with async_session() as session:
            query = (
                select(User)
                .where(User.tags.overlap(self.tags))
                .where(User.experience_id == self.experience_id)
            )

            if self.salary:
                if self.salary.get("to"):
                    query = query.filter(self.salary["to"] >= User.salary)
                elif self.salary.get("from"):
                    query = query.filter(self.salary["from"] <= User.salary)

            employers_types_as_dict = await get_employers_types()

            current_employer_type: str = employers_types_as_dict[self.employer_type_id]

            query = query.where(
                User.desired_employer_type_names.contains([current_employer_type])
            )

            suitable_users: ChunkedIteratorResult[User] = await session.execute(query)

            return suitable_users


async def get_vacancy_by_id(vacancy_id: int) -> Vacancy or None:
    async with async_session() as session:
        vacancy: ChunkedIteratorResult[Vacancy] = await session.execute(
            select(Vacancy).where(Vacancy.hh_id == vacancy_id)
        )

        return vacancy.scalar_one_or_none()


async def get_unsent_vacancies() -> ChunkedIteratorResult[Vacancy]:
    async with async_session() as session:
        vacancies: ChunkedIteratorResult[Vacancy] = await session.execute(
            select(Vacancy).where(Vacancy.is_sent == False)
        )
        return vacancies


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reviewer_telegram_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), nullable=False
    )
    admin_telegram_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), nullable=True
    )
    resolved: Mapped[DateTime] = mapped_column(DateTime, unique=False, nullable=True)
    description: Mapped[str] = mapped_column(Text, unique=False, nullable=False)

    async def add(self):
        async with async_session() as session:
            existing_review: ChunkedIteratorResult[Review] = await session.execute(
                select(Review).where(Review.description == self.description)
            )
            if not existing_review.scalar_one_or_none():
                session.add(self)
                await session.commit()

    async def resolve(self, admin_telegram_id: int, resolution_date: datetime.datetime):
        """Добавлет review дату разрешения => делает его разрешенным"""
        async with async_session() as session:
            await session.execute(
                update(Review)
                .where(Review.id == self.id)
                .values(
                    {
                        "admin_telegram_id": admin_telegram_id,
                        "resolved": resolution_date,
                    }
                )
            )

            await session.commit()


async def get_random_review() -> Review:
    """Достаёт любой Review из соответствующей таблицы, чтобы направить админу для разрешения"""
    async with async_session() as session:
        unsolved_reviews: ChunkedIteratorResult[Review] = await session.execute(
            select(Review).where(Review.resolved == None)
        )

        return unsolved_reviews.first()[0]


async def get_review_by_id(review_id: int) -> Review:
    """Достаёт конкретный Review по id"""
    async with async_session() as session:
        unsolved_reviews: ChunkedIteratorResult[Review] = await session.execute(
            select(Review).where(Review.id == review_id)
        )

        return unsolved_reviews.scalar_one()
