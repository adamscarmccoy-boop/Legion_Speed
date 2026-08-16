import ray
from datetime import datetime
from typing import List
from pydantic import ValidationError
from work_lead_schemas import (
    ScrapedPage, CandidateLead, WorkLeadClean, WorkLeadScore, 
    WorkLeadRecord, RejectedLeadRecord, ScrapeRunProof, 
    WorkSourceType, LeadStatus
)
from work_lead_tables import WorkLeadTableManager

@ray.remote
class IndependentWorkFinderActor:
    def __init__(self):
        self.db_manager = WorkLeadTableManager()
        self.rejected_buffer: List[RejectedLeadRecord] = []
        self.accepted_buffer: List[WorkLeadRecord] = []

    def _scrape_page(self, url: str) -> ScrapedPage:
        # Implementation of actual scraping goes here
        # MUST return a valid ScrapedPage model, no loose dicts.
        pass

    def _parse_candidate(self, page: ScrapedPage) -> List[CandidateLead]:
        # Implementation of chunking/parsing goes here
        # MUST return a list of valid CandidateLead models.
        pass

    def _clean_and_validate(self, candidate: CandidateLead) -> WorkLeadClean:
        # Clean logic. If it fails, raise ValueError to trigger rejection.
        pass

    def _score_lead(self, clean_lead: WorkLeadClean) -> WorkLeadScore:
        # Execute the deterministic scoring formula here
        pass

    def _finalize_record(self, clean: WorkLeadClean, score: WorkLeadScore) -> WorkLeadRecord:
        # Merge clean data and score into the final LanceDB-ready record
        pass

    def run_search(self, seed_urls: List[str], query: str, limit: int = 50) -> ScrapeRunProof:
        start_time = datetime.now()
        self.rejected_buffer.clear()
        self.accepted_buffer.clear()
        errors = []

        for url in seed_urls:
            try:
                # Stage 1: Scrape
                page: ScrapedPage = self._scrape_page(url)
                
                # Stage 2: Parse
                candidates: List[CandidateLead] = self._parse_candidate(page)

                for candidate in candidates:
                    try:
                        # Stage 3: Clean
                        clean_lead: WorkLeadClean = self._clean_and_validate(candidate)
                        
                        # Stage 4: Score
                        lead_score: WorkLeadScore = self._score_lead(clean_lead)
                        
                        # Stage 5: Finalize
                        final_record: WorkLeadRecord = self._finalize_record(clean_lead, lead_score)
                        self.accepted_buffer.append(final_record)

                    except (ValidationError, ValueError) as e:
                        # Catch schema violations and route to rejection log
                        rejection = RejectedLeadRecord(
                            source_url=url,
                            candidate_id=candidate.candidate_id,
                            failed_stage="validation_or_cleaning",
                            validation_error=str(e),
                            raw_text_snippet=candidate.raw_text[:200],
                            rejected_at=datetime.now()
                        )
                        self.rejected_buffer.append(rejection)

            except Exception as e:
                errors.append(f"Failed processing {url}: {str(e)}")

        # Enforce write to LanceDB ONLY via accepted models
        if self.accepted_buffer:
            self.db_manager.save_leads(self.accepted_buffer)
            
        self.db_manager.save_rejections(self.rejected_buffer)

        # Stage 8: Run Proof
        proof = ScrapeRunProof(
            run_id=f"run_{start_time.strftime('%Y%m%d%H%M%S')}",
            start_time=start_time,
            end_time=datetime.now(),
            urls_attempted=len(seed_urls),
            pages_scraped=len(seed_urls) - len(errors),
            candidates_parsed=len(self.accepted_buffer) + len(self.rejected_buffer),
            leads_accepted=len(self.accepted_buffer),
            leads_rejected=len(self.rejected_buffer),
            errors=errors,
            status="COMPLETED" if not errors else "PARTIAL_FAIL"
        )
        self.db_manager.save_run_summary(proof)
        self.db_manager.export_latest_proof()
        
        return proof