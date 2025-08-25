CREATE INDEX idx_signals_callid ON signals(call_message_id);

CREATE INDEX idx_signals_pair ON signals(pair);

CREATE INDEX idx_signals_status ON signals(status);

CREATE INDEX idx_updates_sid ON signal_updates(signal_id);

CREATE INDEX idx_updates_uid ON signal_updates(update_message_id);

CREATE TABLE signal_updates (
            signal_id TEXT,
            channel_id INTEGER,
            update_message_id INTEGER,
            message_link TEXT,
            update_type TEXT,
            price REAL,
            update_at TEXT,
            raw_text TEXT,
            reply_to_msg_id INTEGER,
            linked_msg_id INTEGER,
            PRIMARY KEY (channel_id, update_message_id, update_type)
        );

CREATE TABLE signals (
            signal_id TEXT PRIMARY KEY,
            channel_id INTEGER,
            call_message_id INTEGER UNIQUE,
            message_link TEXT,
            pair TEXT, entry REAL,
            target1 REAL, target2 REAL, target3 REAL, target4 REAL,
            stop1 REAL, stop2 REAL,
            risk_level TEXT,
            volume_rank_num INTEGER, volume_rank_den INTEGER,
            created_at TEXT,
            status TEXT,
            raw_text TEXT, text_sha1 TEXT,
            edit_date TEXT
        );

