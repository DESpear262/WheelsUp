# Flight School Source Discovery Pipeline
#
# This module discovers and seeds flight school data sources from configured
# directories and databases, producing a unique list of school URLs with
# canonical identifiers for deduplication.

import json
import logging
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import hashlib
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SeedDiscoveryResult:
    """
    Result of source discovery and seeding process.
    """

    def __init__(self,
                 source_name: str,
                 source_url: str,
                 source_type: str,
                 discovered_schools: List[Dict[str, Any]],
                 discovery_metadata: Dict[str, Any],
                 processing_time: float = 0.0,
                 errors: Optional[List[str]] = None):
        """
        Initialize discovery result.

        Args:
            source_name: Name of the data source
            source_url: Base URL of the source directory
            source_type: Type of source (directory, certified_directory, etc.)
            discovered_schools: List of discovered school records
            discovery_metadata: Metadata about the discovery process
            processing_time: Time taken to process (seconds)
            errors: List of errors encountered
        """
        self.source_name = source_name
        self.source_url = source_url
        self.source_type = source_type
        self.discovered_schools = discovered_schools
        self.discovery_metadata = discovery_metadata
        self.processing_time = processing_time
        self.errors = errors or []
        self.discovery_timestamp = datetime.now().isoformat()

    @property
    def discovery_success(self) -> bool:
        """Check if discovery was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def total_schools_discovered(self) -> int:
        """Get total number of schools discovered."""
        return len(self.discovered_schools)

    @property
    def unique_domains(self) -> int:
        """Get number of unique domains discovered."""
        domains = set()
        for school in self.discovered_schools:
            if school.get('canonical_domain'):
                domains.add(school['canonical_domain'])
        return len(domains)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'source_name': self.source_name,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'discovery_timestamp': self.discovery_timestamp,
            'total_schools_discovered': self.total_schools_discovered,
            'unique_domains': self.unique_domains,
            'discovered_schools': self.discovered_schools,
            'discovery_metadata': self.discovery_metadata,
            'processing_time': self.processing_time,
            'errors': self.errors,
            'discovery_success': self.discovery_success,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, output_dir: str = "output", filename: Optional[str] = None) -> str:
        """
        Save discovery result to JSON file.

        Args:
            output_dir: Directory to save the file
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to the saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        if not filename:
            # Generate filename based on source and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = self.source_name.replace(' ', '_').replace('/', '_')
            filename = f"seed_discovery_{safe_name}_{timestamp}.json"

        filepath = output_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        logger.info(f"Saved seed discovery result to {filepath}")
        return str(filepath)


class SourceSeedGenerator:
    """
    Generates seed data from configured flight school directory sources.

    This class reads the sources.yaml configuration and produces seed URLs
    and canonical identifiers for flight school discovery.
    """

    def __init__(self, sources_config_path: str = "configs/sources.yaml"):
        """
        Initialize the seed generator.

        Args:
            sources_config_path: Path to sources configuration file
        """
        self.sources_config_path = Path(sources_config_path)
        self.sources_config = self._load_sources_config()

        logger.info(f"Source seed generator initialized with config: {sources_config_path}")

    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML file."""
        try:
            with open(self.sources_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded sources configuration with {len(config.get('sources', []))} sources")
            return config
        except Exception as e:
            error_msg = f"Failed to load sources config: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def generate_source_seeds(self) -> List[SeedDiscoveryResult]:
        """
        Generate seed data for all configured sources.

        Returns:
            List of SeedDiscoveryResult objects for each source
        """
        results = []

        for source_config in self.sources_config.get('sources', []):
            result = self._process_source(source_config)
            results.append(result)

        return results

    def _process_source(self, source_config: Dict[str, Any]) -> SeedDiscoveryResult:
        """Process a single source configuration."""
        start_time = datetime.now()

        source_name = source_config['name']
        source_url = source_config['url']
        source_type = source_config['type']

        logger.info(f"Processing source: {source_name}")

        try:
            # For now, generate basic seed data from configuration
            # In a full implementation, this would crawl the actual directories
            discovered_schools = self._generate_seed_schools(source_config)

            # Calculate discovery metadata
            discovery_metadata = {
                'source_config': source_config,
                'estimated_schools': source_config.get('estimated_schools', 0),
                'data_format': source_config.get('data_format', 'unknown'),
                'crawl_method': source_config.get('crawl_method', 'unknown'),
                'priority': source_config.get('priority', 'unknown'),
                'robots_allowed': source_config.get('robots_allowed', True),
                'duplicate_detection': self._analyze_duplicates(discovered_schools),
            }

            processing_time = (datetime.now() - start_time).total_seconds()

            return SeedDiscoveryResult(
                source_name=source_name,
                source_url=source_url,
                source_type=source_type,
                discovered_schools=discovered_schools,
                discovery_metadata=discovery_metadata,
                processing_time=processing_time,
            )

        except Exception as e:
            error_msg = f"Source processing failed for {source_name}: {str(e)}"
            logger.error(error_msg)

            return SeedDiscoveryResult(
                source_name=source_name,
                source_url=source_url,
                source_type=source_type,
                discovered_schools=[],
                discovery_metadata={'error': error_msg},
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=[error_msg],
            )

    def _generate_seed_schools(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate seed school records from source configuration.

        This is a placeholder implementation. In production, this would:
        1. Crawl the actual directory websites
        2. Extract individual school URLs and contact info
        3. Parse HTML to find school listings
        """
        source_name = source_config['name']
        source_url = source_config['url']

        # For now, generate placeholder seed data based on source type
        # This represents what would be discovered by actual crawling

        seed_schools = []

        if source_config.get('type') == 'directory':
            # Generate sample schools that might be found in a directory
            sample_count = min(source_config.get('estimated_schools', 50) // 10, 10)  # Sample subset
            for i in range(sample_count):
                domain = f"sample-school-{i}.com"
                school = {
                    'school_name': f"Sample Flight School {i+1}",
                    'source_url': f"{source_url}/school-{i+1}",
                    'canonical_domain': domain,
                    'canonical_phone': f"(555) 123-{1000+i:04d}",
                    'icao_code': f"KF{i+1:02d}" if i < 99 else None,
                    'discovery_method': 'configuration_placeholder',
                    'confidence_score': 0.5,  # Placeholder confidence
                    'source_name': source_name,
                    'discovered_at': datetime.now().isoformat(),
                }
                seed_schools.append(school)

        elif source_config.get('type') == 'certified_directory':
            # For certified directories, generate more structured data
            sample_count = min(source_config.get('estimated_schools', 100) // 20, 5)
            for i in range(sample_count):
                domain = f"certified-school-{i}.edu"
                school = {
                    'school_name': f"FAA Certified Flight School {i+1}",
                    'source_url': f"{source_url}/certified-school-{i+1}",
                    'canonical_domain': domain,
                    'canonical_phone': f"(800) FAA-{1000+i:04d}",
                    'icao_code': f"KCF{i+1:02d}",
                    'certification_level': 'Part 141',
                    'discovery_method': 'certified_directory_placeholder',
                    'confidence_score': 0.8,
                    'source_name': source_name,
                    'discovered_at': datetime.now().isoformat(),
                }
                seed_schools.append(school)

        else:
            # For other source types, minimal placeholder
            school = {
                'school_name': f"Placeholder from {source_name}",
                'source_url': source_url,
                'canonical_domain': self._extract_domain(source_url),
                'canonical_phone': None,
                'icao_code': None,
                'discovery_method': 'source_type_placeholder',
                'confidence_score': 0.1,
                'source_name': source_name,
                'discovered_at': datetime.now().isoformat(),
            }
            seed_schools.append(school)

        return seed_schools

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None

    def _analyze_duplicates(self, schools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze potential duplicates in discovered schools."""
        domains = {}
        phones = {}
        icao_codes = {}

        for school in schools:
            # Count domain occurrences
            domain = school.get('canonical_domain')
            if domain:
                domains[domain] = domains.get(domain, 0) + 1

            # Count phone occurrences
            phone = school.get('canonical_phone')
            if phone:
                phones[phone] = phones.get(phone, 0) + 1

            # Count ICAO code occurrences
            icao = school.get('icao_code')
            if icao:
                icao_codes[icao] = icao_codes.get(icao, 0) + 1

        duplicate_domains = {k: v for k, v in domains.items() if v > 1}
        duplicate_phones = {k: v for k, v in phones.items() if v > 1}
        duplicate_icao = {k: v for k, v in icao_codes.items() if v > 1}

        return {
            'total_schools': len(schools),
            'unique_domains': len(domains),
            'unique_phones': len(phones),
            'unique_icao_codes': len(icao_codes),
            'duplicate_domains': duplicate_domains,
            'duplicate_phones': duplicate_phones,
            'duplicate_icao_codes': duplicate_icao,
            'duplicate_domain_count': len(duplicate_domains),
            'duplicate_phone_count': len(duplicate_phones),
            'duplicate_icao_count': len(duplicate_icao),
        }

    def save_batch_summary(self, results: List[SeedDiscoveryResult], output_dir: str = "output") -> str:
        """Save summary of batch seed generation."""
        summary = {
            'batch_timestamp': datetime.now().isoformat(),
            'total_sources_processed': len(results),
            'successful_discoveries': len([r for r in results if r.discovery_success]),
            'total_schools_discovered': sum(r.total_schools_discovered for r in results),
            'total_unique_domains': sum(r.unique_domains for r in results),
            'sources': [],
            'errors': [],
        }

        for result in results:
            source_summary = {
                'source_name': result.source_name,
                'source_type': result.source_type,
                'schools_discovered': result.total_schools_discovered,
                'unique_domains': result.unique_domains,
                'processing_time': result.processing_time,
                'success': result.discovery_success,
            }
            summary['sources'].append(source_summary)

            if result.errors:
                summary['errors'].extend(result.errors)

        # Save summary
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        summary_file = output_path / f"seed_discovery_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved seed discovery summary to {summary_file}")
        return str(summary_file)


# Convenience functions
def generate_all_seeds(output_dir: str = "output") -> List[SeedDiscoveryResult]:
    """
    Generate seeds for all configured sources and save results.

    Args:
        output_dir: Directory to save output files

    Returns:
        List of discovery results
    """
    generator = SourceSeedGenerator()
    results = generator.generate_source_seeds()

    # Save individual results
    for result in results:
        result.save_to_file(output_dir)

    # Save batch summary
    generator.save_batch_summary(results, output_dir)

    return results


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("Starting flight school source discovery...")
    results = generate_all_seeds()

    print(f"\nDiscovery complete!")
    print(f"Sources processed: {len(results)}")
    print(f"Successful discoveries: {len([r for r in results if r.discovery_success])}")
    print(f"Total schools discovered: {sum(r.total_schools_discovered for r in results)}")
    print(f"Total unique domains: {sum(r.unique_domains for r in results)}")

    # Print summary for each source
    for result in results:
        print(f"\n{result.source_name}:")
        print(f"  - Type: {result.source_type}")
        print(f"  - Schools discovered: {result.total_schools_discovered}")
        print(f"  - Unique domains: {result.unique_domains}")
        print(f"  - Success: {result.discovery_success}")
        if result.errors:
            print(f"  - Errors: {len(result.errors)}")
