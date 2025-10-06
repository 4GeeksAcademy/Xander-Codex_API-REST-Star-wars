from flask_sqlalchemy import SQLAlchemy
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    favorites_list: Mapped[List["Favorites"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "favorites_list": [fav.serialize() for fav in self.favorites_list]
        }


class Favorites(db.Model):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_name: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="favorites_list")

    def __repr__(self) -> str:
        return f"<Favorite {self.target_type}:{self.target_name} (User {self.user_id})>"

    def get_target_favorite(self) -> Optional[object]:
        """Devuelve la instancia del objeto favorito (People o Planets)."""
        if self.target_type == "people":
            return db.session.get(People, self.target_id)
        if self.target_type == "planets":
            return db.session.get(Planets, self.target_id)
        return None

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "user_id": self.user_id
        }


class People(db.Model):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hair_color: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<People {self.name}>"

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "hair_color": self.hair_color
        }


class Planets(db.Model):
    __tablename__ = "planets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    diameter: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<Planet {self.name}>"

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "diameter": self.diameter
        }
