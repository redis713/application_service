from app.extensions import db

class Program(db.Model):
    __tablename__ = "programs"

    id = db.Column(db.Integer, primary_key=True)

    # Уникальный код категории/программы (например 'fulltime_cat1', 'fulltime_fire_cat27')
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)

    title = db.Column(db.Text, nullable=False)
    hours = db.Column(db.Integer, nullable=True)

    # Направление: gochs, fire, 112, antiterror
    direction = db.Column(db.String(50), nullable=False, default="gochs", index=True)
    # Форма: distant, ochno, both
    study_form = db.Column(db.String(50), nullable=False, default="both")

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Связи
    listener_courses = db.relationship("ListenerCourse", back_populates="program", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Program {self.code}: {self.title[:30]} ({self.hours} ч.)>"
