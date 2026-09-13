#!/usr/bin/env bash
python3 "$(dirname "$0")/crg_session_start.py" "$@" 2>/dev/null || python "$(dirname "$0")/crg_session_start.py" "$@" 2>/dev/null || echo '{"suppressOutput": true}'
exit 0
