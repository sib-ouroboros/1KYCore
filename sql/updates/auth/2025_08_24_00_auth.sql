-- Shared table: preserve existing IP bindings when this update is reapplied.
CREATE TABLE IF NOT EXISTS `toolip` (
  `ip` varchar(15) NOT NULL DEFAULT '127.0.0.1'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
