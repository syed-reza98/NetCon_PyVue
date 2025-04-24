from models.user import db

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    # Many-to-Many relationship with Role
    roles = db.relationship('Role', secondary='role_permissions', backref='permissions')
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class RolePermissions(db.Model):
    __tablename__ = 'role_permissions'
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)