class WorkflowExecutionService:
    @staticmethod
    def get_execution_steps(workflow_id):
        return {
            "workflow_id": workflow_id,
            "agents": [
                { "id": "planner", "name": "Planner Agent", "desc": "Orchestrating workflow execution steps" },
                { "id": "portfolio", "name": "Portfolio Agent", "desc": "Fetching current asset allocation and holdings" },
                { "id": "market", "name": "Market Agent", "desc": "Downloading live market feeds and ticker data" },
                { "id": "news", "name": "News Analysis Agent", "desc": "Scanning global sentiment and breaking financial news" },
                { "id": "financial", "name": "Financial Agent", "desc": "Running quantitative financial models" },
                { "id": "risk", "name": "Risk Agent", "desc": "Calculating downside exposure and volatility metrics" },
                { "id": "memory", "name": "Memory Systems", "desc": "Retrieving historical user preferences and embeddings" },
                { "id": "rlhf", "name": "RLHF Agent", "desc": "Applying reward model feedback alignments" },
                { "id": "recommendation", "name": "Recommendation Agent", "desc": "Synthesizing final actionable trade strategy" },
            ],
            "tasks": [
                { "id": 1, "name": "Read Portfolio from PostgreSQL", "status": "Completed", "progress": "100%", "time": "0.3 sec" },
                { "id": 2, "name": "Download Live Market Feeds", "status": "Running", "progress": "67%", "time": "1.4 sec" },
                { "id": 3, "name": "Analyze News & Sentiment Matrix", "status": "Waiting", "progress": "0%", "time": "-" },
                { "id": 4, "name": "LangGraph State Aggregation", "status": "Waiting", "progress": "0%", "time": "-" }
            ]
        }