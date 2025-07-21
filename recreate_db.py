"""
Database recreation script for SmartCare AI Chatbot.
Drops all existing tables and recreates them with the current schema.
Use this when you need to reset the database or after schema changes.
"""

from app import app, db

with app.app_context():
    # Drop all tables
    db.drop_all()
    print("Dropped all tables")
    
    # Create all tables with new schema
    db.create_all()
    print("Created all tables with new schema including sources column")
    
    print("Database recreated successfully!") 