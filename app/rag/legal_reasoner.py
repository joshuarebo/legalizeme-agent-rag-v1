"""
Legal Reasoning Components - Specialized components for legal reasoning in Kenya Law
"""
from typing import Dict, List, Any, Optional, Tuple
import re
import json
import os
from app.utils.logger import get_logger
from app.utils.llm_factory import get_llm

logger = get_logger(__name__)

class LegalReasoner:
    """
    Specialized component for legal reasoning in Kenyan law.
    
    Features:
    - Step-by-step reasoning process (IRAC: Issue, Rule, Analysis, Conclusion)
    - Citation tracking and validation
    - Legal principle validation
    - Explanation generation
    - Confidence scoring
    """
    
    def __init__(self):
        """Initialize the legal reasoner."""
        # Load the legal LLM
        self.llm = get_llm(os.getenv("LEGAL_REASONING_LLM", "mixtral"))
        
        # Load legal principles for validation
        self.legal_principles = self._load_legal_principles()
        
    def _load_legal_principles(self) -> Dict[str, Any]:
        """Load Kenyan legal principles for validation."""
        try:
            principles_path = os.path.join(os.getenv("DATA_DIR", "./data"), "legal_principles.json")
            if os.path.exists(principles_path):
                with open(principles_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default principles if file doesn't exist
                return {
                    "constitutional": [
                        "Sovereignty of the people",
                        "Supremacy of the Constitution",
                        "Separation of powers",
                        "Rule of law",
                        "Human dignity",
                        "Equity and inclusiveness",
                        "Equality and non-discrimination",
                        "Human rights protection"
                    ],
                    "contract": [
                        "Offer and acceptance",
                        "Consideration",
                        "Intention to create legal relations",
                        "Capacity to contract",
                        "Legality of object"
                    ],
                    "criminal": [
                        "Presumption of innocence",
                        "Burden of proof",
                        "Right to fair trial",
                        "Legality principle (nullum crimen sine lege)",
                        "Double jeopardy protection"
                    ],
                    "civil": [
                        "Balance of probabilities",
                        "Duty of care",
                        "Remoteness of damage",
                        "Contributory negligence"
                    ],
                    "interpretative": [
                        "Literal rule",
                        "Golden rule",
                        "Mischief rule",
                        "Purposive approach"
                    ]
                }
        except Exception as e:
            logger.error(f"Error loading legal principles: {str(e)}")
            return {}
    
    async def analyze(self, query: str, context: str) -> Dict[str, Any]:
        """
        Perform a complete legal analysis using the IRAC method.
        
        Args:
            query: The legal question
            context: The context containing relevant legal information
            
        Returns:
            Dict containing the analysis components
        """
        # Step 1: Identify the legal issues
        issues = await self._identify_issues(query, context)
        
        # Step 2: Identify applicable rules
        rules = await self._identify_rules(issues, context)
        
        # Step 3: Apply rules to facts (analysis)
        analysis = await self._apply_rules(issues, rules, query, context)
        
        # Step 4: Form conclusion
        conclusion = await self._form_conclusion(analysis)
        
        # Step 5: Extract citations
        citations = self._extract_citations(context, analysis)
        
        # Step 6: Validate legal principles
        principle_validation = self._validate_legal_principles(analysis, rules)
        
        # Step 7: Generate confidence score
        confidence = self._calculate_confidence(issues, rules, analysis, citations, principle_validation)
        
        # Step 8: Generate explanation
        explanation = await self._generate_explanation(issues, rules, analysis, conclusion, confidence)
        
        return {
            "issues": issues,
            "rules": rules,
            "analysis": analysis,
            "conclusion": conclusion,
            "citations": citations,
            "principle_validation": principle_validation,
            "confidence": confidence,
            "explanation": explanation
        }
    
    async def _identify_issues(self, query: str, context: str) -> List[str]:
        """Identify the legal issues from the query and context."""
        try:
            prompt = f"""As a legal expert in Kenyan law, identify the main legal issues in this query:

            Query: {query}

            Context: {context[:1000]}...

            List the specific legal issues (maximum 3) that need to be addressed. Focus on the core legal questions, not factual disputes.
            Format: Return only a numbered list of issues."""
            
            response = await self.llm.invoke(prompt)
            
            # Extract issues as a list
            issues = []
            for line in response.split('\n'):
                line = line.strip()
                if re.match(r'^\d+\.', line):  # Matches lines starting with a number and period
                    issues.append(line)
            
            return issues if issues else [f"Legal issue regarding: {query}"]
        except Exception as e:
            logger.error(f"Error identifying issues: {str(e)}")
            return [f"Legal issue regarding: {query}"]
    
    async def _identify_rules(self, issues: List[str], context: str) -> List[Dict[str, str]]:
        """Identify applicable legal rules for the issues."""
        try:
            issues_text = "\n".join(issues)
            prompt = f"""As a legal expert in Kenyan law, identify the specific legal rules that apply to these issues:

            Issues:
            {issues_text}

            Context: {context[:2000]}...

            For each issue, identify:
            1. The specific legal rule that applies (statute, case law, or principle)
            2. The source of the rule
            3. Any relevant conditions or tests

            Format your response as a list of rules with their sources."""
            
            response = await self.llm.invoke(prompt)
            
            # Parse rules into structured format
            rules = []
            current_rule = {}
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if re.match(r'^\d+\.', line) or "Rule:" in line:
                    # New rule found, save the previous one if it exists
                    if current_rule and "rule" in current_rule:
                        rules.append(current_rule)
                    current_rule = {"rule": line}
                elif "Source:" in line or "source:" in line:
                    current_rule["source"] = line.split(":", 1)[1].strip()
                elif "Test:" in line or "test:" in line or "Conditions:" in line or "conditions:" in line:
                    current_rule["test"] = line.split(":", 1)[1].strip()
                elif current_rule:
                    # Add to the last field
                    if "test" in current_rule:
                        current_rule["test"] += " " + line
                    elif "source" in current_rule:
                        current_rule["source"] += " " + line
                    else:
                        current_rule["rule"] += " " + line
            
            # Add the last rule if it exists
            if current_rule and "rule" in current_rule:
                rules.append(current_rule)
            
            return rules
        except Exception as e:
            logger.error(f"Error identifying rules: {str(e)}")
            return [{"rule": "General legal principles", "source": "Kenyan law"}]
    
    async def _apply_rules(self, issues: List[str], rules: List[Dict[str, str]], query: str, context: str) -> str:
        """Apply the identified rules to the facts (analysis)."""
        try:
            issues_text = "\n".join(issues)
            rules_text = "\n".join([f"Rule {i+1}: {rule.get('rule', '')}\nSource: {rule.get('source', '')}" 
                                    for i, rule in enumerate(rules)])
            
            prompt = f"""As a legal expert in Kenyan law, apply the identified rules to the facts in this query:

            Query: {query}

            Issues:
            {issues_text}

            Applicable Rules:
            {rules_text}

            Context (facts and relevant law):
            {context[:3000]}...

            Provide a detailed analysis showing how each rule applies to the specific facts of this situation.
            Your analysis should connect the rules to specific elements in the query and context."""
            
            analysis = await self.llm.invoke(prompt)
            return analysis
        except Exception as e:
            logger.error(f"Error in rule application: {str(e)}")
            return "Unable to perform detailed analysis due to technical issues."
    
    async def _form_conclusion(self, analysis: str) -> str:
        """Form a legal conclusion based on the analysis."""
        try:
            prompt = f"""Based on the following legal analysis, provide a clear, concise legal conclusion:

            Analysis:
            {analysis}

            Your conclusion should directly address the legal issues identified and provide a definitive legal position based on Kenyan law.
            Be specific about the legal outcome."""
            
            conclusion = await self.llm.invoke(prompt)
            return conclusion
        except Exception as e:
            logger.error(f"Error forming conclusion: {str(e)}")
            return "Based on the available information and Kenyan law, a definitive conclusion cannot be provided."
    
    def _extract_citations(self, context: str, analysis: str) -> List[Dict[str, str]]:
        """Extract and validate legal citations from the context and analysis."""
        combined_text = f"{context}\n{analysis}"
        citations = []
        
        # Patterns for different citation types
        patterns = {
            "case": [
                r'\[(\d{4})\]\s+(\w+)',              # [2022] eKLR
                r'(\w+)\s+v\.?\s+(\w+)',             # Party v Party
                r'(?:Civil|Criminal)\s+(?:Appeal|Case|Petition)\s+No\.\s+(\d+)\s+of\s+(\d{4})' # Civil Appeal No. X of YYYY
            ],
            "statute": [
                r'(?:The\s+)?(\w+\s+Act)(?:\s+No\.\s+\d+\s+of\s+\d{4})?',  # Employment Act / Act No. X of YYYY
                r'Constitution of Kenya,?\s+(?:Article|Section)?\s+(\d+)',  # Constitution articles
                r'(?:Article|Section)\s+(\d+)\s+of\s+(?:the\s+)?(\w+)',     # Sections of Acts
            ]
        }
        
        # Extract citations
        for citation_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        citation_text = " ".join(match)
                    else:
                        citation_text = match
                    
                    # Create URL for Kenya Law
                    if citation_type == "case":
                        url = f"https://new.kenyalaw.org/search?query={citation_text.replace(' ', '+')}"
                    else:
                        url = f"https://new.kenyalaw.org/legislation/?search={citation_text.replace(' ', '+')}"
                    
                    citations.append({
                        "text": citation_text,
                        "type": citation_type,
                        "url": url
                    })
        
        # Remove duplicates
        unique_citations = []
        seen = set()
        for citation in citations:
            citation_key = f"{citation['text']}|{citation['type']}"
            if citation_key not in seen:
                seen.add(citation_key)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _validate_legal_principles(self, analysis: str, rules: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate that the analysis adheres to Kenyan legal principles."""
        validation_results = {
            "adherence_to_principles": True,
            "identified_principles": [],
            "missing_principles": [],
            "conflicts": []
        }
        
        # Extract all principles mentioned in rules and analysis
        rule_texts = " ".join([rule.get("rule", "") + " " + rule.get("source", "") for rule in rules])
        all_text = analysis + " " + rule_texts
        
        # Check for principle mentions
        for category, principles in self.legal_principles.items():
            for principle in principles:
                if re.search(r'\b' + re.escape(principle) + r'\b', all_text, re.IGNORECASE):
                    validation_results["identified_principles"].append({
                        "principle": principle,
                        "category": category
                    })
        
        # Check for potential conflicts
        conflicting_pairs = [
            ("presumption of innocence", "balance of probabilities"),
            ("literal rule", "purposive approach"),
            ("contributory negligence", "duty of care")
        ]
        
        for principle1, principle2 in conflicting_pairs:
            if (re.search(r'\b' + re.escape(principle1) + r'\b', all_text, re.IGNORECASE) and
                re.search(r'\b' + re.escape(principle2) + r'\b', all_text, re.IGNORECASE)):
                validation_results["conflicts"].append({
                    "principle1": principle1,
                    "principle2": principle2,
                    "description": f"Potential conflict between {principle1} and {principle2}"
                })
                validation_results["adherence_to_principles"] = False
        
        return validation_results
    
    def _calculate_confidence(self, issues: List[str], rules: List[Dict[str, str]], 
                             analysis: str, citations: List[Dict[str, str]], 
                             principle_validation: Dict[str, Any]) -> float:
        """Calculate confidence score for the legal reasoning."""
        score = 0.5  # Start with neutral confidence
        
        # Factor 1: Issue clarity
        if issues and len(issues) > 0:
            score += 0.05
        
        # Factor 2: Rule identification
        if rules and len(rules) > 0:
            score += min(0.1, len(rules) * 0.03)
        
        # Factor 3: Citations
        if citations:
            score += min(0.15, len(citations) * 0.03)
        
        # Factor 4: Analysis depth (estimated by length)
        if analysis:
            analysis_words = len(analysis.split())
            if analysis_words > 500:
                score += 0.1
            elif analysis_words > 200:
                score += 0.05
        
        # Factor 5: Principle adherence
        if principle_validation["adherence_to_principles"]:
            score += 0.1
        else:
            score -= 0.1
        
        # Factor 6: Identified principles
        score += min(0.1, len(principle_validation["identified_principles"]) * 0.02)
        
        # Factor 7: Conflicts (negative impact)
        score -= min(0.2, len(principle_validation["conflicts"]) * 0.1)
        
        # Ensure score is within 0-1 range
        return max(0.1, min(0.99, score))
    
    async def _generate_explanation(self, issues: List[str], rules: List[Dict[str, str]], 
                                  analysis: str, conclusion: str, confidence: float) -> str:
        """Generate a clear explanation of the reasoning process."""
        try:
            # Format issues and rules for prompt
            issues_text = "\n".join([f"- {issue}" for issue in issues])
            rules_text = "\n".join([f"- {rule.get('rule', '')}" for rule in rules])
            
            confidence_level = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"
            
            prompt = f"""As a legal expert, explain the legal reasoning for this analysis in clear, simple language:

            Issues identified:
            {issues_text}

            Legal rules applied:
            {rules_text}

            Analysis:
            {analysis[:500]}...

            Conclusion:
            {conclusion[:200]}...

            Confidence level: {confidence_level}

            Provide a clear, step-by-step explanation of how the legal reasoning works, suitable for a non-lawyer to understand.
            Focus on the core logic and avoid technical jargon where possible."""
            
            explanation = await self.llm.invoke(prompt)
            return explanation
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return "The legal analysis examines the facts in light of Kenyan law and relevant precedents to arrive at a conclusion on the legal issues presented."

import os  # Adding the missing import
