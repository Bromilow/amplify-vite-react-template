from datetime import datetime
from app import db


class DocumentTemplate(db.Model):
    """Document template model for managing system document templates"""
    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False, unique=True)
    filename = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship to User
    uploader = db.relationship('User', backref=db.backref('uploaded_templates', lazy='dynamic'))
    
    def __repr__(self):
        return f'<DocumentTemplate {self.document_type}: {self.filename}>'
    
    def to_dict(self):
        """Convert document template to dictionary"""
        return {
            'id': self.id,
            'document_type': self.document_type,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.first_name + ' ' + self.uploader.last_name if self.uploader else 'Unknown'
        }