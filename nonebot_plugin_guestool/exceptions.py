class GuestoolError(Exception):
    pass


class MatcherError(GuestoolError):
    pass


class RuleParseError(MatcherError):
    pass


class RuleCreateError(MatcherError):
    pass


class MatcherHackError(MatcherError):
    pass


class ModelValidateError(GuestoolError):
    pass