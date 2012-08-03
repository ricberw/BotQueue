SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;

CREATE TABLE `activities` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL,
  `activity` text NOT NULL,
  `action_date` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `comments` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL,
  `comment` text NOT NULL,
  `comment_date` datetime NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `email_queue` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL default '0',
  `subject` varchar(255) NOT NULL,
  `text_body` text NOT NULL,
  `html_body` text NOT NULL,
  `to_email` varchar(255) NOT NULL,
  `to_name` varchar(255) NOT NULL,
  `queue_date` datetime NOT NULL,
  `sent_date` datetime NOT NULL,
  `status` enum('queued','sent') NOT NULL default 'queued',
  UNIQUE KEY `id` (`id`),
  KEY `user_id` (`user_id`),
  KEY `status` (`status`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `s3_files` (
  `id` bigint(11) unsigned NOT NULL auto_increment,
  `type` varchar(255) NOT NULL,
  `size` int(10) unsigned NOT NULL,
  `hash` char(32) NOT NULL,
  `bucket` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  `add_date` datetime NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `shortcodes` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `url` varchar(255) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `url` (`url`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `tokens` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL,
  `hash` varchar(40) NOT NULL,
  `expire_date` datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `pass_hash` (`hash`),
  KEY `expire_date` (`expire_date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `users` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `username` varchar(32) NOT NULL,
  `email` varchar(255) NOT NULL,
  `pass_hash` varchar(40) NOT NULL,
  `pass_reset_hash` char(40) NOT NULL,
  `location` varchar(255) NOT NULL,
  `birthday` date NOT NULL,
  `last_active` datetime NOT NULL,
  `registered_on` datetime NOT NULL,
  `is_admin` tinyint(1) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `last_active` (`last_active`),
  KEY `username` (`username`),
  KEY `pass_hash` (`pass_hash`),
  KEY `email` (`email`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;