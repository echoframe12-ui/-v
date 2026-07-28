"""Tests for review.py — ReviewEngine functionality.

Covers:
  - submit() creates pending review
  - approve() updates status to approved
  - approve() on unknown proposal raises KeyError
  - list_reviews() returns all submitted reviews
  - list_reviews() returns copy of internal list
"""
import unittest

from review import ReviewEngine


class ReviewEngineTests(unittest.TestCase):

    def test_submit_creates_pending_review(self):
        engine = ReviewEngine()
        review = engine.submit("Add feature X", "reviewer_a")
        self.assertEqual(review["proposal"], "Add feature X")
        self.assertEqual(review["reviewer"], "reviewer_a")
        self.assertEqual(review["status"], "pending")
        self.assertEqual(len(engine.list_reviews()), 1)

    def test_approve_existing_proposal(self):
        engine = ReviewEngine()
        engine.submit("Proposal 1", "rev_1")
        approved = engine.approve("Proposal 1")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(engine.list_reviews()[0]["status"], "approved")

    def test_approve_unknown_proposal_raises_keyerror(self):
        engine = ReviewEngine()
        engine.submit("Proposal 1", "rev_1")
        with self.assertRaises(KeyError):
            engine.approve("Nonexistent Proposal")

    def test_list_reviews(self):
        engine = ReviewEngine()
        self.assertEqual(engine.list_reviews(), [])
        engine.submit("p1", "r1")
        engine.submit("p2", "r2")
        self.assertEqual(len(engine.list_reviews()), 2)

    def test_list_reviews_returns_copy(self):
        engine = ReviewEngine()
        engine.submit("p1", "r1")
        reviews = engine.list_reviews()
        reviews.append({"proposal": "fake", "reviewer": "fake", "status": "fake"})
        self.assertEqual(len(engine.list_reviews()), 1)


if __name__ == "__main__":
    unittest.main()

