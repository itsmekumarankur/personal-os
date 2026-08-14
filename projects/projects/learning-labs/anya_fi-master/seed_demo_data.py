#!/usr/bin/env python3
"""Seed sample data for demoing Anya.fi."""

from app.db.database import get_db_context
from app.db.models import User, Goal, Transaction, GoalType, GoalStatus, TransactionCategory
from datetime import datetime, timedelta

def seed_data():
    with get_db_context() as db:
        # Check if test user exists
        user = db.query(User).filter(User.telegram_id == "demo_user").first()
        if not user:
            user = User(
                telegram_id="demo_user",
                phone="9876543210",
                name="Anya Tester"
            )
            db.add(user)
            db.flush()
            print(f"Created user: {user.name} (ID: {user.id})")
        
        # Check existing goals
        existing_goals = db.query(Goal).filter(Goal.user_id == user.id).all()
        if not existing_goals:
            goal1 = Goal(
                user_id=user.id,
                goal_type=GoalType.SAVING,
                title="Goa Vacation & New Laptop",
                target_amount=60000.0,
                current_amount=25000.0,
                month_nonessential_budget=15000.0,
                status=GoalStatus.ACTIVE,
                thumbnail_url="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=500"
            )
            goal2 = Goal(
                user_id=user.id,
                goal_type=GoalType.EMERGENCY_FUND,
                title="Emergency Savings Fund",
                target_amount=100000.0,
                current_amount=45000.0,
                month_nonessential_budget=10000.0,
                status=GoalStatus.ACTIVE
            )
            db.add_all([goal1, goal2])
            print("Created sample goals")

        # Check existing transactions
        existing_txs = db.query(Transaction).filter(Transaction.user_id == user.id).all()
        if not existing_txs:
            now = datetime.utcnow()
            tx1 = Transaction(
                user_id=user.id,
                amount=450.0,
                merchant="Starbucks",
                category=TransactionCategory.FOOD,
                is_essential=False,
                timestamp=now - timedelta(days=1)
            )
            tx2 = Transaction(
                user_id=user.id,
                amount=1200.0,
                merchant="Zomato Gourmet",
                category=TransactionCategory.FOOD,
                is_essential=False,
                timestamp=now - timedelta(days=2)
            )
            tx3 = Transaction(
                user_id=user.id,
                amount=3500.0,
                merchant="Myntra Fashion",
                category=TransactionCategory.SHOPPING,
                is_essential=False,
                timestamp=now - timedelta(days=3)
            )
            tx4 = Transaction(
                user_id=user.id,
                amount=850.0,
                merchant="Uber Ride",
                category=TransactionCategory.TRANSPORT,
                is_essential=True,
                timestamp=now - timedelta(days=4)
            )
            db.add_all([tx1, tx2, tx3, tx4])
            print("Created sample transactions")

        print("✅ Demo Data Seeding Complete!")

if __name__ == "__main__":
    seed_data()
