ALTER TABLE Videos ADD COLUMN IsUpload INTEGER DEFAULT 0 NULL;
ALTER TABLE Videos ADD COLUMN IsDownload INTEGER DEFAULT 0 NULL;
ALTER TABLE Videos ADD COLUMN ChannelId TEXT DEFAULT '' NULL;
ALTER TABLE SubscribeChannels ADD COLUMN LastPullLatestDate DATETIME NULL;
