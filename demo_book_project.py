#!/usr/bin/env python3
"""
Trinity Life Assistant - Book Project Demo
===========================================

Interactive demonstration of the complete Trinity Life Assistant workflow:
- Phase 1: Ambient listening detects "coaching book" pattern
- Phase 2: Trinity asks proactive question, user says YES
- Phase 3: Project initialization, daily execution, completion

Usage:
    python demo_book_project.py

Constitutional Compliance:
- Article I: Complete context before action
- Article II: 100% verification (all tests pass)
- Article III: Automated enforcement (budget/foundation)
- Article IV: Continuous learning (preference optimization)
- Article V: Spec-driven development (formal spec creation)
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt, Confirm

# Trinity Protocol imports
from trinity_protocol.core.models.patterns import DetectedPattern, PatternType
from trinity_protocol.core.models.project import (
    Project, ProjectState, QASession, QAQuestion, QAAnswer,
    ProjectSpec, ProjectPlan, ProjectTask, TaskStatus, ProjectMetadata
)
from trinity_protocol.project_initializer import ProjectInitializer
from trinity_protocol.spec_from_conversation import SpecFromConversation
from trinity_protocol.project_executor import ProjectExecutor
from trinity_protocol.daily_checkin import DailyCheckin
from shared.type_definitions.result import Result, Ok, Err

console = Console()


class BookProjectDemo:
    """Interactive demo of Trinity Life Assistant book project workflow."""

    def __init__(self):
        """Initialize demo with mock components."""
        self.user_name = "Alex"
        self.console = Console()
        self.pattern: Optional[DetectedPattern] = None
        self.qa_session: Optional[QASession] = None
        self.spec: Optional[ProjectSpec] = None
        self.plan: Optional[ProjectPlan] = None
        self.project: Optional[Project] = None
        self.day_count = 0

    async def run(self):
        """Run complete demo workflow."""
        self.console.clear()

        # Welcome
        self.show_welcome()

        # Phase 1: Ambient Detection
        await self.demo_ambient_detection()

        # Phase 2: Proactive Question
        await self.demo_proactive_question()

        # Phase 3: Project Initialization
        await self.demo_project_initialization()

        # Phase 3: Daily Execution (simulate 14 days)
        await self.demo_daily_execution()

        # Completion
        await self.demo_project_completion()

        # Summary
        self.show_summary()

    def show_welcome(self):
        """Display welcome message."""
        welcome_text = """
[bold cyan]Trinity Life Assistant - Book Project Demo[/bold cyan]

This demo simulates the complete workflow of using Trinity to finish
a coaching book in 2 weeks with minimal time investment.

[yellow]What You'll See:[/yellow]
1. 🎤 Ambient listening detects your book project pattern
2. 💬 Trinity asks if you want help (you say YES!)
3. 📝 7-question initialization (takes ~10 minutes)
4. 📋 Formal specification generation
5. 📅 14 days of daily check-ins (1-3 questions each)
6. 📚 Complete book delivered

[green]Total Time Investment: ~70-140 minutes over 2 weeks[/green]
[green]Value Created: Complete coaching book ready for publishing[/green]

Press Enter to begin the demo...
"""
        console.print(Panel(welcome_text, border_style="cyan"))
        input()

    async def demo_ambient_detection(self):
        """Demo Phase 1: Ambient listener detects pattern."""
        console.print("\n[bold]═══ Phase 1: Ambient Intelligence ═══[/bold]\n")

        # Simulate conversation over a day
        conversations = [
            ("9:30 AM", "Morning coffee", "I really need to finish my coaching book..."),
            ("11:45 AM", "Client call", "My book project is weighing on me."),
            ("2:15 PM", "Lunch break", "I wish I could just get the book done."),
            ("4:30 PM", "Afternoon work", "That coaching book won't write itself."),
            ("6:00 PM", "Evening review", "Need to make progress on the book this month."),
        ]

        console.print("[dim]🎤 Trinity is listening (privacy-first, 100% local)...[/dim]\n")

        for time, context, phrase in conversations:
            console.print(f"[cyan]{time}[/cyan] | [dim]{context}[/dim]")
            console.print(f'  You: "[italic]{phrase}[/italic]"')
            await asyncio.sleep(0.5)

        # Pattern detected
        console.print("\n[yellow]🔍 WITNESS Pattern Detector: ANALYZING...[/yellow]")
        await asyncio.sleep(1)

        self.pattern = DetectedPattern(
            pattern_id="pattern_book_001",
            pattern_type=PatternType.PROJECT_MENTION,
            topic="coaching book",
            confidence=0.92,
            mention_count=5,
            first_mention=datetime.now(timezone.utc) - timedelta(hours=8),
            last_mention=datetime.now(timezone.utc),
            context_summary="User mentioned coaching book project 5 times today with emotional weight (weighing on me, wish I could finish)"
        )

        console.print("\n[bold green]✅ Pattern Detected![/bold green]")

        # Show pattern details
        pattern_table = Table(show_header=False, border_style="green")
        pattern_table.add_column("Property", style="cyan")
        pattern_table.add_column("Value", style="white")

        pattern_table.add_row("Type", "Project Mention (recurring topic)")
        pattern_table.add_row("Topic", "coaching book")
        pattern_table.add_row("Mentions", "5 times today")
        pattern_table.add_row("Confidence", "92%")
        pattern_table.add_row("Context", "Emotional signals detected (frustration, urgency)")

        console.print(pattern_table)

        console.print("\n[dim]Press Enter to see Trinity's response...[/dim]")
        input()

    async def demo_proactive_question(self):
        """Demo Phase 2: Trinity asks proactive question."""
        console.print("\n[bold]═══ Phase 2: Proactive Assistance ═══[/bold]\n")

        # Trinity formulates question
        console.print("[yellow]🤔 ARCHITECT is formulating a question...[/yellow]")
        await asyncio.sleep(1)

        question_text = """
[bold cyan]Trinity:[/bold cyan] Hi Alex! I noticed you mentioned your coaching book
5 times today. I can help you finish it in [green]2 weeks[/green] with just
[green]1-3 questions per day[/green] (total time: ~2 hours over 14 days).

Here's how it works:
  • I'll ask 7 quick setup questions now (~10 minutes)
  • You'll get a formal project plan to review
  • Each morning, I'll check in with 2-3 questions
  • I'll handle research, drafting, and organizing
  • In 14 days: complete book ready for Amazon KDP

Want to hear more about the plan?
"""
        console.print(Panel(question_text, border_style="cyan", title="💬 Proactive Question"))

        # User response
        response = Confirm.ask("\n[bold]Your response (YES/NO/LATER)[/bold]", default=True)

        if not response:
            console.print("\n[yellow]📝 Understood! I've noted you're not interested in this right now.[/yellow]")
            console.print("[dim]This helps Trinity learn what you value.[/dim]")
            sys.exit(0)

        console.print("\n[bold green]✅ Great! Let's get started.[/bold green]")
        console.print("[dim]Press Enter to begin project initialization...[/dim]")
        input()

    async def demo_project_initialization(self):
        """Demo Phase 3: Project initialization via Q&A."""
        console.print("\n[bold]═══ Phase 3: Project Initialization ═══[/bold]\n")

        # Q&A Session
        console.print("[cyan]📝 Quick Setup Questions (7 questions, ~10 minutes)[/cyan]\n")

        questions_and_answers = [
            (
                "What's the core message or theme of your coaching book?",
                "Helping coaches build sustainable 6-figure practices without burnout"
            ),
            (
                "Who is your target audience?",
                "New and intermediate coaches (1-5 years experience) who struggle with client acquisition and pricing"
            ),
            (
                "How many chapters are you envisioning?",
                "8 chapters: Mindset, Positioning, Pricing, Marketing, Sales, Delivery, Systems, Scale"
            ),
            (
                "What's already written vs. needs to be written?",
                "I have rough outlines for 3 chapters, nothing fully drafted. Need everything written from scratch."
            ),
            (
                "What's your preferred writing style?",
                "Conversational, practical, lots of real examples. Like 'Company of One' meets 'The Coaching Habit'"
            ),
            (
                "Any specific case studies or stories to include?",
                "Yes - my journey from $30k to $300k, 3 client success stories, common pricing mistakes"
            ),
            (
                "What's your ideal completion timeline?",
                "2 weeks would be amazing. Need it done before my course launch in 3 weeks."
            ),
        ]

        qa_questions = []
        qa_answers = []

        for i, (question, answer) in enumerate(questions_and_answers, 1):
            console.print(f"[bold cyan]Q{i}:[/bold cyan] {question}")

            # Simulate user thinking
            with Progress(
                SpinnerColumn(),
                TextColumn("[dim]Waiting for your answer...[/dim]"),
                transient=True
            ) as progress:
                progress.add_task("thinking", total=None)
                await asyncio.sleep(0.8)

            console.print(f"[green]You:[/green] {answer}\n")

            # Store Q&A
            qa_questions.append(QAQuestion(
                question_id=f"q{i}",
                question_text=question,
                question_number=i,
                required=True
            ))
            qa_answers.append(QAAnswer(
                answer_id=f"a{i}",
                question_id=f"q{i}",
                answer_text=answer,
                answered_at=datetime.now(timezone.utc)
            ))

            await asyncio.sleep(0.3)

        # Create QA Session
        self.qa_session = QASession(
            session_id="session_book_001",
            project_id="proj_book_001",
            pattern_id=self.pattern.pattern_id,
            pattern_type=self.pattern.pattern_type,
            questions=qa_questions,
            answers=qa_answers,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            completed_at=datetime.now(timezone.utc),
            status="completed"
        )

        # Generate spec
        console.print("[yellow]🔄 Generating formal specification...[/yellow]")
        await asyncio.sleep(2)

        self.spec = self.create_mock_spec()

        console.print("\n[bold green]✅ Specification Generated![/bold green]")
        self.show_spec_preview()

        # Approval
        console.print("\n[dim]Press Enter to approve specification...[/dim]")
        input()

        console.print("[green]✓[/green] Specification approved!\n")

        # Generate plan
        console.print("[yellow]📅 Creating 14-day implementation plan...[/yellow]")
        await asyncio.sleep(2)

        self.plan = self.create_mock_plan()
        self.project = self.create_mock_project()

        console.print("\n[bold green]✅ Plan Created![/bold green]")
        self.show_plan_preview()

        console.print("\n[dim]Press Enter to approve plan and start execution...[/dim]")
        input()

        console.print("[green]✓[/green] Plan approved! Starting daily execution.\n")

    async def demo_daily_execution(self):
        """Demo Phase 3: Daily execution with check-ins."""
        console.print("\n[bold]═══ Phase 3: Daily Execution (14 Days) ═══[/bold]\n")
        console.print("[dim]Simulating daily check-ins... (press Enter to advance through days)[/dim]\n")

        daily_checkins = [
            # Days 1-2: Chapter 1 (Mindset)
            (1, "Morning! Ready to start?", [
                ("Should Chapter 1 focus more on mindset shifts or tactical exercises?", "60/40 mindset to tactical"),
                ("Any specific limiting beliefs coaches struggle with?", "Charging enough, imposter syndrome")
            ]),
            (2, "Chapter 1 progress check", [
                ("How's the opening story landing?", "Great! More vulnerable than I expected"),
                ("Ready for Chapter 2 outline review?", "Yes, let's see it")
            ]),

            # Days 3-4: Chapter 2 (Positioning)
            (3, "Chapter 2 begins", [
                ("What differentiates elite coaches from beginners?", "Specialization and confident pricing"),
            ]),
            (4, "Positioning refinement", [
                ("Should we include your positioning framework diagram?", "Absolutely, that's valuable"),
                ("Any client examples for this chapter?", "Sarah's rebrand story")
            ]),

            # Days 5-6: Chapter 3 (Pricing)
            (5, "The pricing chapter", [
                ("What's your strongest pricing argument?", "Value-based vs. hourly - coaches leave money on table"),
                ("Include the $10k package case study?", "Yes, that converts well")
            ]),
            (6, "Pricing examples", [
                ("How many pricing tiers to recommend?", "3 tiers: starter, signature, premium")
            ]),

            # Days 7-8: Chapters 4-5 (Marketing & Sales)
            (7, "Marketing chapter", [
                ("Inbound vs outbound focus?", "80% inbound (content), 20% outbound (partnerships)"),
                ("Top 3 marketing channels?", "LinkedIn, podcast guesting, referrals")
            ]),
            (8, "Sales process", [
                ("Include your discovery call script?", "Yes! That's gold")
            ]),

            # Days 9-10: Chapters 6-7 (Delivery & Systems)
            (9, "Delivery chapter", [
                ("Group vs 1-on-1 coaching balance?", "Start 1-on-1, add group at $50k+"),
            ]),
            (10, "Systems & automation", [
                ("Which tools to recommend?", "Keep it simple: Calendly, Stripe, Notion")
            ]),

            # Days 11-12: Chapter 8 (Scale)
            (11, "Scaling strategies", [
                ("When to hire first team member?", "$150k revenue, 80%+ capacity"),
                ("Passive income products?", "Course after proven 1-on-1 success")
            ]),
            (12, "Final chapter polish", [
                ("How to end the book?", "Your journey + invitation to implement")
            ]),

            # Days 13-14: Polish & Completion
            (13, "Final review", [
                ("Any sections need expansion?", "Chapter 5 - add more objection handling"),
            ]),
            (14, "Ready to ship?", [
                ("Book feels complete?", "Yes! Better than I imagined"),
                ("Ready for Amazon KDP formatting?", "Absolutely")
            ]),
        ]

        for day_num, greeting, questions in daily_checkins:
            self.day_count = day_num

            # Daily check-in header
            console.print(f"\n[bold cyan]═══ Day {day_num}/14 - {datetime.now().strftime('%A, %B %d')} ═══[/bold cyan]")
            console.print(f"[cyan]Trinity:[/cyan] {greeting}\n")

            # Questions for the day
            for q_num, (question, answer) in enumerate(questions, 1):
                console.print(f"  [cyan]Q{q_num}:[/cyan] {question}")

                # Simulate response time
                await asyncio.sleep(0.5)

                console.print(f"  [green]You:[/green] {answer}\n")
                await asyncio.sleep(0.3)

            # Progress update
            progress_pct = (day_num / 14) * 100
            console.print(f"[dim]📊 Progress: {progress_pct:.0f}% complete ({day_num}/14 days)[/dim]")

            # Simulate work being done
            if day_num % 2 == 0:
                console.print(f"[dim]📝 Chapter {day_num // 2} draft completed overnight[/dim]")

            console.print("[dim]───────────────────────────────────────[/dim]")

            # Wait for user to advance
            if day_num < 14:
                input()

    async def demo_project_completion(self):
        """Demo project completion and deliverable."""
        console.print("\n\n[bold]═══ Project Completion ═══[/bold]\n")

        console.print("[yellow]🎉 Generating final deliverable...[/yellow]")
        await asyncio.sleep(2)

        completion_panel = """
[bold green]✅ YOUR COACHING BOOK IS COMPLETE![/bold green]

[cyan]📚 Deliverable:[/cyan]
  • 8 complete chapters (52,000 words)
  • Professional formatting (ready for KDP)
  • Cover design recommendations
  • Marketing copy for Amazon listing

[cyan]📊 Project Stats:[/cyan]
  • Duration: 14 days
  • Check-ins: 14 daily sessions
  • Your time invested: 94 minutes total
  • Questions answered: 31 total
  • Chapters completed: 8 of 8

[cyan]💎 What's Included:[/cyan]
  ✓ Complete manuscript (Word + PDF)
  ✓ Chapter-by-chapter breakdown
  ✓ Amazon KDP upload guide
  ✓ Launch marketing plan
  ✓ Reader lead magnet ideas

[cyan]📈 Ready For:[/cyan]
  ✓ Amazon KDP publishing
  ✓ Course pre-launch funnel
  ✓ Authority positioning
  ✓ Client acquisition

[bold green]The book that was "weighing on you" is now DONE.[/bold green]
[dim]From idea → finished book in 14 days with <2 hours time investment.[/dim]
"""
        console.print(Panel(completion_panel, border_style="green", title="🎉 SUCCESS"))

        console.print("\n[dim]Press Enter for project summary...[/dim]")
        input()

    def show_spec_preview(self):
        """Show specification preview."""
        spec_preview = f"""
[bold]Project Specification: Coaching Book[/bold]

[cyan]Title:[/cyan] {self.spec.title}

[cyan]Goals:[/cyan]
  • Complete 8-chapter coaching business book
  • Ready for Amazon KDP publishing
  • Practical, actionable content with case studies
  • Finished in 14 days

[cyan]Target Audience:[/cyan]
  • New/intermediate coaches (1-5 years exp)
  • Struggling with client acquisition and pricing
  • Want to build sustainable 6-figure practice

[cyan]Success Criteria:[/cyan]
  • 8 complete chapters drafted
  • 50,000+ words total
  • 5+ case studies included
  • Professional formatting complete
  • User approves final manuscript

[cyan]Timeline:[/cyan] 14 days (2 weeks)
[cyan]Daily Commitment:[/cyan] ~5-10 minutes (answering 1-3 questions)
"""
        console.print(Panel(spec_preview, border_style="blue", title="📋 Specification Preview"))

    def show_plan_preview(self):
        """Show implementation plan preview."""
        plan_preview = """
[bold]14-Day Implementation Plan[/bold]

[cyan]Phase 1: Foundation (Days 1-2)[/cyan]
  • Chapter 1: Mindset - Draft and refine

[cyan]Phase 2: Positioning & Pricing (Days 3-6)[/cyan]
  • Chapter 2: Positioning - Framework and examples
  • Chapter 3: Pricing - Strategy and case studies

[cyan]Phase 3: Acquisition (Days 7-8)[/cyan]
  • Chapter 4: Marketing - Content strategy
  • Chapter 5: Sales - Discovery and closing

[cyan]Phase 4: Delivery & Systems (Days 9-10)[/cyan]
  • Chapter 6: Delivery - 1-on-1 and group coaching
  • Chapter 7: Systems - Automation and tools

[cyan]Phase 5: Scale & Polish (Days 11-14)[/cyan]
  • Chapter 8: Scale - Team and passive income
  • Final polish, formatting, KDP prep

[cyan]Daily Pattern:[/cyan]
  • Morning check-in (8:30 AM - learned from your preferences)
  • 1-3 questions to guide next chapter
  • Overnight: Trinity drafts content
  • Next morning: Review and refine
"""
        console.print(Panel(plan_preview, border_style="magenta", title="📅 Implementation Plan"))

    def show_summary(self):
        """Show final summary."""
        console.print("\n\n[bold]═══ Demo Summary ═══[/bold]\n")

        summary_table = Table(title="Trinity Life Assistant - By The Numbers", border_style="cyan")
        summary_table.add_column("Metric", style="cyan", width=40)
        summary_table.add_column("Value", style="green", width=30)

        summary_table.add_row("Duration", "14 days (2 weeks)")
        summary_table.add_row("Your Time Investment", "~94 minutes total")
        summary_table.add_row("Daily Time Commitment", "5-10 minutes per day")
        summary_table.add_row("Questions Answered", "31 total (7 setup + 24 daily)")
        summary_table.add_row("Chapters Completed", "8 of 8 (100%)")
        summary_table.add_row("Total Words Written", "~52,000 words")
        summary_table.add_row("Value Created", "Complete publishable book")
        summary_table.add_row("Traditional Timeline", "6-12 months (if ever finished)")
        summary_table.add_row("Trinity Timeline", "14 days")
        summary_table.add_row("Time Saved", "Hundreds of hours")

        console.print(summary_table)

        roi_panel = """
[bold green]Return on Investment:[/bold green]

[cyan]Traditional Approach:[/cyan]
  • 6-12 months of procrastination
  • 100-200 hours of writing time
  • Likely never finished
  • Opportunity cost: $50k-$100k in lost revenue

[cyan]Trinity Approach:[/cyan]
  • 14 days start to finish
  • < 2 hours of your time
  • Guaranteed completion
  • Book fuels course launch (3 weeks)

[bold]This is the Trinity Life Assistant vision: realized.[/bold]
"""
        console.print(Panel(roi_panel, border_style="green", title="💰 ROI Analysis"))

        console.print("\n[bold cyan]What makes this possible:[/bold cyan]")
        console.print("  [green]✓[/green] Phase 1: Ambient listening detects your real needs")
        console.print("  [green]✓[/green] Phase 2: Proactive questions at the right time")
        console.print("  [green]✓[/green] Phase 3: Structured execution with minimal overhead")
        console.print("  [green]✓[/green] Constitutional compliance: Quality guaranteed")
        console.print("  [green]✓[/green] Learning: Gets better with every interaction\n")

    def create_mock_spec(self) -> ProjectSpec:
        """Create mock specification."""
        from trinity_protocol.core.models.project import AcceptanceCriterion

        return ProjectSpec(
            spec_id="spec_book_001",
            project_id="proj_book_001",
            qa_session_id=self.qa_session.session_id,
            title="Complete Coaching Business Book: Sustainable 6-Figure Practice",
            description="A practical guide for new and intermediate coaches to build sustainable 6-figure practices without burnout",
            goals=[
                "Complete 8-chapter book on coaching business building",
                "Include real case studies and practical examples",
                "Ready for Amazon KDP publishing",
                "Finished in 14 days with minimal time investment"
            ],
            non_goals=[
                "Not a certification program",
                "Not focused on life coaching techniques",
                "Not about personal development"
            ],
            user_personas=[
                "Alex: Experienced coach wanting to share knowledge",
                "Reader: New coach struggling with business side"
            ],
            acceptance_criteria=[
                AcceptanceCriterion(
                    criterion_id="ac_1",
                    description="8 chapters completed with 50,000+ words total",
                    verification_method="Word count verification"
                ),
                AcceptanceCriterion(
                    criterion_id="ac_2",
                    description="5+ real case studies included throughout",
                    verification_method="Manual review"
                ),
                AcceptanceCriterion(
                    criterion_id="ac_3",
                    description="Professional formatting ready for KDP upload",
                    verification_method="KDP compliance check"
                ),
                AcceptanceCriterion(
                    criterion_id="ac_4",
                    description="User approval of final manuscript",
                    verification_method="User approval"
                )
            ],
            constraints=[
                "14-day timeline (hard deadline for course launch)",
                "User has max 10 minutes per day available",
                "Must maintain conversational, practical tone"
            ],
            spec_markdown="# Coaching Book Specification\n\n## Goals\n...\n## Personas\n...\n## Acceptance Criteria\n...\n(Full spec content would be here, 100+ characters)",
            created_at=datetime.now(timezone.utc),
            approval_status="approved"
        )

    def create_mock_plan(self) -> ProjectPlan:
        """Create mock plan."""
        tasks = [
            ProjectTask(
                task_id=f"task_{i}",
                project_id="proj_book_001",
                title=f"Chapter {(i//2)+1} - {'Draft' if i%2==0 else 'Polish'}",
                description=f"Complete chapter {(i//2)+1}",
                estimated_minutes=30,
                assigned_to="system",
                status=TaskStatus.PENDING
            )
            for i in range(14)
        ]

        return ProjectPlan(
            plan_id="plan_book_001",
            project_id="proj_book_001",
            spec_id=self.spec.spec_id,
            tasks=tasks,
            total_estimated_days=14,
            daily_questions_avg=2,
            timeline_end_estimate=datetime.now(timezone.utc) + timedelta(days=14),
            plan_markdown="# 14-Day Implementation Plan\n\n## Overview\n...\n## Daily Breakdown\n...\n(Full plan content here, 100+ characters)"
        )

    def create_mock_project(self) -> Project:
        """Create mock project."""
        return Project(
            project_id="proj_book_001",
            user_id="user_alex",
            title="Coaching Business Book",
            description="Complete practical guide for building sustainable 6-figure coaching practice",
            state=ProjectState.EXECUTING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata=ProjectMetadata(
                topic="coaching book",
                estimated_completion=datetime.now(timezone.utc) + timedelta(days=14),
                daily_time_commitment_minutes=10
            )
        )


async def main():
    """Run demo."""
    try:
        demo = BookProjectDemo()
        await demo.run()

        console.print("\n[bold green]Demo complete! 🎉[/bold green]")
        console.print("\n[cyan]To experience this for real:[/cyan]")
        console.print("  1. Deploy Trinity Life Assistant")
        console.print("  2. Start ambient listening")
        console.print("  3. Mention your book project naturally")
        console.print("  4. Say YES when Trinity asks")
        console.print("  5. Answer questions daily for 14 days")
        console.print("  6. Get your complete book\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted. Thanks for watching![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
