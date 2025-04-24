from models.user import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    def has_permission(self, permission_name):
        return any(p.name == permission_name for p in self.permissions)