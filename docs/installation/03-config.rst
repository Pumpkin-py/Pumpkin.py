Configuration
=============

SSH connections
---------------

Connecting to remote server by using username and password gets annoying really fast. That's why there are SSH keys. You only have to create the key and then tell the SSH to use it when connecting to your server.

.. code-block:: bash

	ssh-keygen -t ed25519
	# save the file as something descriptive, e.g. /home/<username>/.ssh/pumpkin_server
	# you can omit the password by pressing Enter twice

Then add the key to the SSH configuration file (``~/.ssh/config``), so it knows when to use it.

.. code-block:: bash

	Host 10.0.0.10
		user discord
		PubkeyAuthentication yes
		IdentitiesOnly yes
		IdentityFile ~/.ssh/pumpkin_server

To use the SSH key on the server, you have to add the contents of the **public** key (e.g. ``/home/<username>/.ssh/pumpkin_server.pub``) to server's ``/home/discord/.ssh/authorized_keys``.

PostgreSQL backups
------------------

The following script makes backup of the database and saves it. If it is the first day of the month, it compresses the previous month, making it much more space-efficient.

.. code-block:: bash

	#!/bin/bash

	backups=~/pumpkin-backups

	mkdir -p $backups
	cd $backups

	# Database inside of Docker
	docker exec -it pumpkin_db_1 pg_dump -c -U postgres > dump_`date +%Y-%m-%d"_"%H:%M:%S`.sql
	# Database running directly on the system
	pg_dump -U <database user name> pumpkin > dump_`date +%Y-%m-%d"_"%H:%M:%S`.sql

	today=$(date +%d)

	if [ $today -eq "01" ]; then
		# compress last month
		month=$(date -d "`date +%Y%m01` -1day" +%Y-%m)
		tar -cJf dump_$month.tar.xz dump_$month*.sql
		rm dump_$month*.sql
	fi

	exit 0

To allow passwordless access to the database (in the non-docker situation), create file ``~/.pgpass`` with the following content: ``hostname:port:database:username:password``

.. code-block::

	localhost:*:<database>:<username>:<password>

The file has to be readable only by the owner:

.. code-block:: bash

	chmod 600 ~/.pgpass

..
	The Docker backup is not tested!

Then you can set up a cron job to run the script every day.

.. code-block::

	# make backup every day at 1 AM
	0 1 * * * bash ~/pumpkin-backup.sh >> ~/pumpkin-backup.log 2>&1

To **restore** the backup, you have to drop the database first, which may require you to login as the ``postgres`` user:

.. code-block::

	psql -U postgres -c "DROP DATABASE <database>;"
	psql -U postgres -c "CREATE DATABASE <database>;"
	psql -U <username> -f <backup file>

Log management
--------------

The logs are stored in ``logs/`` directory.
