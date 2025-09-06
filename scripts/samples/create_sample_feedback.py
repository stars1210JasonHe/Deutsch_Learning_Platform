#!/usr/bin/env python3
"""
Create sample feedback data for testing the automated processing system
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_sample_feedback():
    """Insert sample feedback data into the database"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if we have some words to attach feedback to
    cursor.execute("SELECT id, lemma, pos FROM word_lemmas LIMIT 10")
    words = cursor.fetchall()
    
    if not words:
        print("No words found in database. Please add some words first.")
        return
    
    # Check if we have a user to attach feedback to
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("No users found. Creating a test user...")
        cursor.execute("""
            INSERT INTO users (email, hashed_password, is_active)
            VALUES ('testuser@example.com', 'hashed_password_here', 1)
        """)
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user[0]
    
    # Sample feedback data
    sample_feedbacks = [
        {
            "feedback_type": "incorrect_meaning",
            "description": "The word 'haben' is translated as 'to eat' but it should be 'to have'. This is a basic error.",
            "suggested_correction": "Change the English translation from 'to eat' to 'to have'",
            "current_meaning": "to eat; to consume",
            "current_example": "Ich habe Hunger. (I eat hunger.)"
        },
        {
            "feedback_type": "incorrect_example", 
            "description": "The example sentence for 'gehen' is grammatically incorrect. It should use proper German grammar.",
            "suggested_correction": "Change 'Ich gehen zum Supermarkt' to 'Ich gehe zum Supermarkt'",
            "current_meaning": "to go; to walk",
            "current_example": "Ich gehen zum Supermarkt. (I go to the supermarket.)"
        },
        {
            "feedback_type": "incorrect_grammar",
            "description": "The verb 'sein' is marked as regular but it's actually irregular. This affects conjugation.",
            "suggested_correction": "Change regularity from 'regular' to 'irregular'",
            "current_meaning": "to be; to exist",
            "current_example": "Ich bin müde. (I am tired.)"
        },
        {
            "feedback_type": "incorrect_meaning",
            "description": "The Chinese translation for 'Apfel' is wrong. It shows '桌子' (table) but should be '苹果' (apple).",
            "suggested_correction": "Change Chinese translation from '桌子' to '苹果'",
            "current_meaning": "apple; fruit",
            "current_example": "Der Apfel ist rot. (The apple is red.)"
        },
        {
            "feedback_type": "other",
            "description": "The word 'Buch' is missing the plural form. It should show 'Bücher' as the plural.",
            "suggested_correction": "Add plural form: Bücher",
            "current_meaning": "book; novel",
            "current_example": "Das Buch ist interessant. (The book is interesting.)"
        }
    ]
    
    print("Creating sample feedback data...")
    print("-" * 50)
    
    inserted_count = 0
    
    for i, feedback_data in enumerate(sample_feedbacks):
        if i < len(words):
            word_id, lemma, pos = words[i]
            
            try:
                cursor.execute("""
                    INSERT INTO word_feedback (
                        lemma_id, user_id, feedback_type, description, 
                        suggested_correction, current_meaning, current_example,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (
                    word_id,
                    user_id,
                    feedback_data['feedback_type'],
                    feedback_data['description'],
                    feedback_data['suggested_correction'],
                    feedback_data['current_meaning'],
                    feedback_data['current_example'],
                    datetime.now() - timedelta(hours=random.randint(1, 48))
                ))
                
                inserted_count += 1
                print(f"Created feedback for word: {lemma} ({feedback_data['feedback_type']})")
                
            except Exception as e:
                print(f"Failed to create feedback for {lemma}: {e}")
    
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print(f"Successfully created {inserted_count} sample feedback entries")
    
    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM word_feedback WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Total pending feedback in database: {pending_count}")

def show_sample_data():
    """Display the created sample data"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            f.id,
            w.lemma,
            f.feedback_type,
            f.description,
            f.status
        FROM word_feedback f
        JOIN word_lemmas w ON f.lemma_id = w.id
        WHERE f.status = 'pending'
        ORDER BY f.created_at DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    if results:
        print("\nSample feedback entries created:")
        print("-" * 50)
        for feedback_id, lemma, feedback_type, description, status in results:
            print(f"ID: {feedback_id}")
            print(f"Word: {lemma}")
            print(f"Type: {feedback_type}")
            print(f"Description: {description[:80]}...")
            print(f"Status: {status}")
            print("-" * 30)
    else:
        print("No pending feedback found.")
    
    conn.close()

if __name__ == "__main__":
    print("SAMPLE FEEDBACK DATA CREATOR")
    print("=" * 50)
    create_sample_feedback()
    show_sample_data()
    print("\n" + "=" * 50)
    print("Sample data creation complete!")
    print("Now you can test the feedback processing with:")
    print("  python process_feedback_with_openai.py --report-only")
    print("  python process_feedback_with_openai.py --limit 3")