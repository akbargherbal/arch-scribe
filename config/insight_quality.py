"""
Insight Quality Validation Rules
--------------------------------
Template: [WHAT] using [HOW], which [WHY/IMPACT]

Comprehensive word lists for validating architectural insights.
All words lowercase for case-insensitive matching.

Example: "Implements token refresh using Redis cache with sliding window TTL, 
         which reduces database load by 60% and prevents session timeouts"
"""

# [WHAT] - Action verbs describing system behavior
ACTION_VERBS = [
    # Core actions (fundamental system behaviors)
    'implements', 'provides', 'manages', 'handles', 'defines', 'executes',
    'processes', 'utilizes', 'supports', 'operates', 'maintains', 'governs',
    'enforces', 'generates', 'establishes', 'determines', 'facilitates',
    'coordinates', 'initiates', 'terminates', 'renders', 'abstracts',
    'encapsulates', 'delegates', 'wraps', 'extends', 'overrides',
    
    # Data operations (storage, transformation, retrieval)
    'caches', 'serializes', 'deserializes', 'indexes', 'aggregates', 
    'transforms', 'validates', 'persists', 'retrieves', 'queries', 
    'filters', 'compresses', 'decompresses', 'encrypts', 'decrypts',
    'mutates', 'stores', 'normalizes', 'denormalizes', 'partitions',
    'segments', 'hashes', 'snapshots', 'rehydrates', 'materializes',
    'streams', 'buffers', 'batches', 'merges', 'deduplicates',
    'sanitizes', 'scrubs', 'enriches', 'flattens', 'reshapes',
    
    # Flow control (routing, orchestration, timing)
    'routes', 'dispatches', 'queues', 'schedules', 'throttles', 
    'debounces', 'redirects', 'forwards', 'broadcasts', 'orchestrates',
    'emits', 'mediates', 'arbitrates', 'sequences', 'pipelines',
    'triggers', 'gates', 'defers', 'polls', 'pushes', 'pulls',
    
    # Security & access control
    'authenticates', 'authorizes', 'audits', 'restricts', 'secures',
    'verifies', 'revokes', 'masks', 'signs', 'confines', 'isolates',
    'hardens', 'whitelists', 'blacklists', 'rate-limits', 'challenges',
    
    # Integration & communication (APIs, services, messaging)
    'exposes', 'consumes', 'publishes', 'subscribes', 'integrates',
    'connects', 'interfaces', 'transmits', 'receives', 'proxies',
    'invokes', 'brokers', 'translates', 'adapts', 'bridges',
    'relays', 'multiplexes', 'demultiplexes', 'negotiates',
    
    # State & lifecycle management
    'initializes', 'bootstraps', 'configures', 'migrates', 'syncs',
    'updates', 'patches', 'deletes', 'provisions', 'decommissions',
    'monitors', 'tracks', 'replicates', 'tears down', 'archives',
    'checkpoints', 'resumes', 'suspends', 'resets', 'reconciles',
    'upgrades', 'downgrades', 'rollbacks', 'versions',
    
    # Error handling & resilience
    'retries', 'falls back', 'recovers', 'logs', 'alerts', 'suppresses',
    'degrades', 'circuit-breaks', 'times out', 'handles', 'catches',
    'propagates', 'swallows', 'rethrows', 'quarantines',
    
    # Resource management (allocation, optimization, cleanup)
    'allocates', 'deallocates', 'releases', 'pools', 'limits', 'scales',
    'optimizes', 'recycles', 'meters', 'budgets', 'rebalances',
    'reserves', 'preloads', 'lazy-loads', 'garbage-collects',
    
    # Monitoring & observability
    'traces', 'spans', 'instruments', 'samples', 'profiles', 'measures',
    'reports', 'exports', 'collects', 'aggregates metrics',
]

# [WHY/IMPACT] - Phrases indicating consequences, benefits, or reasoning
IMPACT_WORDS = [
    # Direct causation (explicit connections)
    'which', 'enabling', 'because', 'thereby', 'thus', 'hence',
    'so that', 'resulting in', 'leading to', 'allowing', 'allowing for',
    'due to', 'in order to', 'consequently', 'therefore', 'as a result',
    'to ensure', 'to support', 'to enable', 'by means of', 'via',
    'through which', 'causing', 'producing', 'yielding',
    
    # Performance impacts (speed, efficiency, throughput)
    'reducing latency', 'improving throughput', 'increasing responsiveness',
    'minimizing overhead', 'accelerating', 'optimizing', 'boosting performance',
    'maximizing efficiency', 'reducing processing time', 'decreasing load time',
    'improving concurrency', 'scaling horizontally', 'scaling vertically',
    'handling high load', 'reducing network traffic', 'minimizing i/o',
    'optimizing memory usage', 'reducing cpu usage', 'improving cache hit rate',
    'achieving sub-second response', 'enabling near real-time processing',
    'reducing database queries', 'minimizing round trips',
    
    # Reliability & availability (uptime, fault tolerance)
    'ensuring high availability', 'guaranteeing uptime', 'improving reliability',
    'enhancing stability', 'promoting resilience', 'ensuring fault tolerance',
    'preventing downtime', 'minimizing service disruption',
    'avoiding single points of failure', 'reducing blast radius',
    'isolating failures', 'containing errors', 'gracefully degrading',
    'failing safely', 'recovering quickly', 'self-healing',
    
    # Data quality & consistency (correctness, integrity)
    'maintaining consistency', 'ensuring data integrity', 'guaranteeing atomicity',
    'ensuring durability', 'guaranteeing eventual consistency',
    'preventing data loss', 'avoiding corruption', 'ensuring correctness',
    'maintaining referential integrity', 'enforcing constraints',
    'validating input', 'preventing race conditions', 'ensuring idempotency',
    'avoiding duplicates', 'preserving state', 'maintaining immutability',
    
    # Security & compliance (protection, regulations)
    'protecting against unauthorized access', 'mitigating security risks',
    'hardening the system', 'reducing attack surface', 'ensuring data privacy',
    'preventing injection attacks', 'enforcing least privilege',
    'ensuring compliance', 'supporting audit requirements',
    'protecting sensitive data', 'preventing data leakage',
    'meeting regulatory requirements', 'enforcing access control',
    
    # Scalability & growth (capacity, extensibility)
    'supporting future growth', 'enabling horizontal scaling',
    'facilitating extensibility', 'supporting increased load',
    'accommodating more users', 'handling traffic spikes',
    'preparing for scale', 'future-proofing', 'enabling expansion',
    
    # Maintainability & developer experience
    'simplifying maintenance', 'improving readability', 'reducing complexity',
    'enhancing modularity', 'promoting code reuse', 'standardizing patterns',
    'reducing cognitive load', 'simplifying debugging', 'improving testability',
    'enabling parallel development', 'reducing coupling', 'increasing cohesion',
    'abstracting implementation details', 'simplifying onboarding',
    'reducing boilerplate', 'standardizing interfaces', 'documenting behavior',
    
    # Business value (cost, time-to-market, user experience)
    'reducing operational cost', 'improving time to market',
    'accelerating feature delivery', 'supporting business logic',
    'enabling monetization', 'improving customer experience',
    'reducing total cost of ownership', 'automating manual processes',
    'eliminating toil', 'facilitating rapid iteration', 'supporting compliance',
    'enabling personalization', 'improving user satisfaction',
    'reducing support tickets', 'increasing conversion rates',
    
    # Operational excellence (deployment, monitoring, recovery)
    'facilitating rapid deployment', 'enabling continuous delivery',
    'supporting rollback', 'simplifying disaster recovery',
    'improving observability', 'enabling debugging', 'facilitating auditing',
    'supporting troubleshooting', 'enabling root cause analysis',
    'providing visibility', 'tracking behavior', 'measuring impact',
]

# Quality thresholds
MIN_WORD_COUNT = 15  # Minimum words for a complete insight
MAX_WORD_COUNT = 100  # Maximum to prevent rambling (optional enforcement)

# Optional: Validation strictness levels (for future use)
STRICTNESS_LEVELS = {
    'lenient': {
        'min_words': 10,
        'require_action': True,
        'require_impact': False,
    },
    'standard': {
        'min_words': 15,
        'require_action': True,
        'require_impact': True,
    },
    'strict': {
        'min_words': 20,
        'require_action': True,
        'require_impact': True,
        'require_how': True,  # Future: detect technical implementation details
    }
}