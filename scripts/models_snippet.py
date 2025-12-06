
class SpecialDay(db.Model):
    """SpecialDay model - represents holidays and non-working days"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), default='holiday')  # 'holiday', 'company_event', 'other'
    color = db.Column(db.String(20), nullable=True)  # Hex color code

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'name': self.name,
            'type': self.type,
            'color': self.color
        }

    def __repr__(self):
        return f'<SpecialDay {self.name} {self.date}>'
