"""
Schemas for Github webhook events. These models are incomplete.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, MutableMapping, Optional, Type

import pydantic
from pydantic import UrlStr
from typing_extensions import Literal

AnyDict = Dict[Any, Any]

event_registry: MutableMapping[str, Type["GithubEvent"]] = dict()


def register(cls: Type["GithubEvent"]) -> Type["GithubEvent"]:
    event_registry[cls._event_name] = cls
    return cls


class HookConfiguration(pydantic.BaseModel):
    url: UrlStr
    content_type: str
    insecure_url: Optional[str]


class Hook(pydantic.BaseModel):
    """
    https://developer.github.com/v3/repos/hooks/#get-single-hook
    """

    id: int
    name: str
    events: List[str]
    active: bool
    config: HookConfiguration
    updated_at: datetime
    created_at: datetime


class Installation(pydantic.BaseModel):
    id: int
    node_id: Optional[str]


class GithubEvent(pydantic.BaseModel):
    _event_name: str
    installation: Optional[Installation]


@register
class Ping(GithubEvent):
    """
    https://developer.github.com/webhooks/#ping-event
    """

    _event_name = "ping"
    zen: str
    hook_id: int
    hook: Hook


class UserType(Enum):
    user = "User"
    organization = "Organization"
    bot = "Bot"


class User(pydantic.BaseModel):
    login: str
    id: int
    node_id: str
    url: UrlStr
    type: UserType


class Repo(pydantic.BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    owner: User
    private: bool
    description: Optional[str]
    fork: bool
    url: UrlStr
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    homepage: Optional[str]
    default_branch: str


class CompareBranch(pydantic.BaseModel):
    label: str
    ref: str
    sha: str
    user: User
    repo: Repo


class PullRequestState(Enum):
    open = "open"
    closed = "closed"


class Label(pydantic.BaseModel):
    id: int
    node_id: str
    url: UrlStr
    name: str
    color: str
    default: bool = False


class Milestone(pydantic.BaseModel):
    pass


class BasePullRequest(pydantic.BaseModel):
    url: UrlStr
    id: int
    node_id: str
    number: int
    state: PullRequestState
    locked: bool
    title: str
    user: User
    body: Optional[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    merged_at: Optional[datetime]
    merge_commit_sha: Optional[str]
    assignee: Optional[User]
    assignees: List[User]
    requested_reviewers: List[User]
    # TODO: get response for requested_teams
    requested_teams: List[Any]
    labels: List[Label]
    milestone: Optional[Milestone]
    head: CompareBranch
    base: CompareBranch


class MergeableState(Enum):
    # The pull request is behind target
    behind = "behind"
    blocked = "blocked"
    # The pull request can be merged.
    clean = "clean"
    # The pull request cannot be merged due to merge conflicts.
    conflicting = "dirty"
    # The mergeability of the pull request is still being calculated.
    unknown = "unknown"
    unstable = "unstable"
    draft = "draft"


class PullRequest(BasePullRequest):
    merged: bool
    mergeable: bool
    rebaseable: bool
    mergeable_state: MergeableState
    merged_by: Optional[User]
    comments: int
    review_comments: int
    maintainer_can_modify: bool
    commits: int
    additions: int
    deletions: int
    changed_files: int


class PullRequestEventActions(Enum):
    assigned = "assigned"
    unassigned = "unassigned"
    review_requested = "review_requested"
    review_request_removed = "review_request_removed"
    labeled = "labeled"
    unlabeled = "unlabeled"
    opened = "opened"
    edited = "edited"
    closed = "closed"
    ready_for_review = "ready_for_review"
    locked = "locked"
    unlocked = "unlocked"
    reopened = "reopened"
    synchronize = "synchronize"


@register
class PullRequestEvent(GithubEvent):
    """
    https://developer.github.com/v3/activity/events/types/#pullrequestevent
    """

    _event_name = "pull_request"
    action: PullRequestEventActions
    number: int
    pull_request: PullRequest
    repository: Repo
    sender: User


class PullRequestReviewAction(Enum):
    submitted = "submitted"
    edited = "edited"
    dismissed = "dismissed"


class PullRequestReview(pydantic.BaseModel):
    id: int
    node_id: str
    user: User
    body: Optional[str]
    commit_id: str
    submitted_at: datetime
    state: str


class PullRequestShort(BasePullRequest):
    pass


@register
class PullRequestReviewEvent(GithubEvent):
    """
    https://developer.github.com/v3/activity/events/types/#pullrequestreviewevent
    """

    _event_name = "pull_request_review"
    action: PullRequestReviewAction
    review: PullRequestReview
    pull_request: PullRequestShort
    repository: Repo
    sender: User


class CheckRunStatus(Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"


class CheckRunConclusion(Enum):
    success = "success"
    failure = "failure"
    neutral = "neutral"
    cancelled = "cancelled"
    timed_out = "timed_out"
    action_required = "action_required"


class CheckRunBranchRepo(pydantic.BaseModel):
    id: int
    url: UrlStr
    name: str


class CheckRunBranch(pydantic.BaseModel):
    ref: str
    sha: str
    repo: CheckRunBranchRepo


class CheckRunPR(pydantic.BaseModel):
    url: UrlStr
    id: int
    number: int
    head: CheckRunBranch
    base: CheckRunBranch


class CheckRun(pydantic.BaseModel):
    id: int
    head_sha: str
    external_id: str
    url: UrlStr
    status: CheckRunStatus
    name: str
    conclusion: Optional[CheckRunConclusion]
    pull_requests: List[CheckRunPR]

    def to_status(self) -> Literal["pending", "success", "failure"]:
        if self.status is None:
            return "pending"
        if self.status in (CheckRunConclusion.success, CheckRunConclusion.neutral):
            return "success"
        return "failure"


class CheckRunEventAction(Enum):
    created = "created"
    rerequested = "rerequested"
    completed = "completed"
    requested_action = "requested_action"


@register
class CheckRunEvent(GithubEvent):
    """
    https://developer.github.com/v3/activity/events/types/#checkrunevent
    """

    _event_name = "check_run"
    action: CheckRunEventAction
    check_run: CheckRun
    repository: Repo


class Commiter(pydantic.BaseModel):
    name: str
    email: str
    date: datetime


class Tree(pydantic.BaseModel):
    sha: str
    url: UrlStr


class CommitDetails(pydantic.BaseModel):
    author: Commiter
    commiter: Commiter
    message: str
    tree: Tree
    url: UrlStr
    comment_count: int


class Commit(pydantic.BaseModel):
    sha: str
    node_id: str
    url: UrlStr
    author: Optional[User]
    committer: Optional[User]
    parents: List[Tree]


class Branch(pydantic.BaseModel):
    name: str
    commit: Tree


class StatusEventState(Enum):
    pending = "pending"
    success = "success"
    failure = "failure"
    error = "error"


@register
class StatusEvent(GithubEvent):
    """
    https://developer.github.com/v3/activity/events/types/#statusevent
    """

    _event_name = "status"
    id: int
    sha: str
    name: str
    target_url: Optional[UrlStr]
    context: str
    description: Optional[str]
    state: StatusEventState
    commit: Commit
    branches: List[Branch]
    created_at: datetime
    updated_at: datetime
    repository: Repo
    sender: User


class PushEventCommitter(pydantic.BaseModel):
    name: str
    email: str
    username: str


class PushEventPusher(pydantic.BaseModel):
    name: str
    email: Optional[str]


class PushEventCommit(pydantic.BaseModel):
    id: str
    tree_id: str
    timestamp: datetime
    url: UrlStr
    distinct: bool
    message: str
    author: PushEventCommitter
    committer: PushEventCommitter
    added: List[str]
    removed: List[str]
    modified: List[str]


@register
class PushEvent(GithubEvent):
    """
    https://developer.github.com/v3/activity/events/types/#pushevent
    """

    _event_name = "push"
    ref: str
    before: str
    after: str
    created: bool
    deleted: bool
    forced: bool
    base_ref: Optional[str]
    compare: UrlStr
    commits: List[PushEventCommit]
    head_commit: Optional[PushEventCommit]
    repository: Repo
    pusher: PushEventPusher
    sender: User
