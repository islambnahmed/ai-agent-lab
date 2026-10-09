"""Exact conditional rank-trend test for binary Markov row visits.

For each row and predeclared visit count n, under a stationary binary Markov
null the first n outgoing next-states at that row are iid Bernoulli(p) for
unknown p. Conditional on their total k, all k-subsets of visit positions
are equiprobable. A two-sided exact Mann--Whitney rank-sum test comparing
success vs failure visit positions therefore has superuniform p-values.
Bonferroni over 2*len(checkpoints) tests controls the probability of any
false alarm at alpha, even if tests are dependent. This holds for the
untruncated conceptual row-visit streams; skipping checkpoints because
calendar horizon ended cannot increase the false-alarm probability.

Requires SciPy for exact discrete rank-sum tails. A non-alarm is inconclusive.
"""
from math import isfinite
from functools import lru_cache
from scipy.stats import _mannwhitneyu  # SciPy private helper: prototype, pin/test version

@lru_cache(maxsize=512)
def _rank_cdf(n,k):
    # Exact integer-rank U distribution under random permutation of k successes.
    # Cache by sample sizes to avoid rebuilding distributions per trajectory.
    m=k*(n-k)
    distribution=_mannwhitneyu._MWU(k,n-k)
    return distribution.cdf(__import__('numpy').arange(m//2+1))

def exact_rank_p(n, successes_positions):
    if not isinstance(n,int) or isinstance(n,bool) or n<2:
        raise ValueError('n must be >=2 integer')
    if not isinstance(successes_positions,tuple) or any(not isinstance(i,int) or isinstance(i,bool) for i in successes_positions):
        raise ValueError('positions must be integer tuple')
    if tuple(sorted(set(successes_positions)))!=successes_positions or any(i<1 or i>n for i in successes_positions):
        raise ValueError('invalid positions')
    k=len(successes_positions)
    if k in (0,n):
        return 1.0
    u=sum(successes_positions)-k*(k+1)//2
    tail=min(u,k*(n-k)-u)
    return min(1.0,2.0*float(_rank_cdf(n,k)[tail]))

class RankTrendGuard:
    def __init__(self, checkpoints=(48,96,144,192), alpha=.04, initial_state=0):
        if (not isinstance(alpha,(int,float)) or isinstance(alpha,bool)
                or not isfinite(alpha) or not 0<alpha<1):
            raise ValueError('alpha must be finite and in (0,1)')
        if (not checkpoints or len(set(checkpoints))!=len(checkpoints)
                or any(not isinstance(n,int) or isinstance(n,bool) or n<2 for n in checkpoints)):
            raise ValueError('invalid checkpoints')
        if initial_state not in (0,1) or isinstance(initial_state,bool):
            raise ValueError('initial state must be 0 or 1')
        self.checkpoints=frozenset(checkpoints)
        self.threshold=alpha/(2*len(checkpoints))
        self.last_state=initial_state
        self.rows=[[],[]]
        self.first_alarm=None
        self.tests=[]
        self.t=0

    def step(self, previous, current):
        if (previous not in (0,1) or current not in (0,1)
                or isinstance(previous,bool) or isinstance(current,bool)):
            raise ValueError('binary transition required')
        if previous!=self.last_state:
            raise ValueError('broken stream continuity')
        self.t+=1
        row=self.rows[previous]
        row.append(current)
        n=len(row)
        if n in self.checkpoints:
            p=exact_rank_p(n,tuple(i for i,x in enumerate(row,1) if x==1))
            self.tests.append((self.t,previous,n,p))
            if self.first_alarm is None and p<=self.threshold:
                self.first_alarm=self.t
        self.last_state=current
        return self.first_alarm is not None
