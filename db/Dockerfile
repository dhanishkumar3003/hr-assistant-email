FROM postgres:16

# Debian's tzdata package in this image drops legacy zone aliases
# (Asia/Calcutta, Asia/Bombay, etc), keeping only canonical IANA names
# (Asia/Kolkata). Windows clients (npgsql/JDBC/DBeaver) send the legacy
# alias as the session TimeZone GUC, which Postgres then rejects with
# "invalid value for parameter TimeZone". Symlink it back in.
RUN ln -sf Kolkata /usr/share/zoneinfo/Asia/Calcutta
