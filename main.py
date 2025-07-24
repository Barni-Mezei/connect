import asyncio
import asyncssh # type: ignore
import configparser

class SSHClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None

    async def connect(self):
        try:
            # Establish an SSH connection
            self.connection = await asyncssh.connect(self.host, username=self.username, password=self.password)
            print(f'Connected to {self.host}')
        except Exception as e:
            print(f'Connection failed: {str(e)}')

    async def run_command(self, command):
        if self.connection is None:
            print("Not connected to the SSH server.")
            return

        try:
            # Execute the command
            result = await self.connection.run(command)
            print(f'Standard Output:\n{result.stdout}')
            print(f'Standard Error:\n{result.stderr}')
        except Exception as e:
            print(f'Command execution failed: {str(e)}')

    async def close(self):
        if self.connection:
            await self.connection.close()
            print('Connection closed.')

async def main():
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    config.read('config.ini')
    host = config['DEFAULT']['host']
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']

    ssh_client = SSHClient(host, username, password)
    await ssh_client.connect()

    # Run commands in a loop
    while True:
        command = input("Enter command to execute (or 'exit' to close): ")
        if command.lower() == 'exit':
            break
        await ssh_client.run_command(command)

    await ssh_client.close()

# Run the main function using asyncio
if __name__ == '__main__':
    asyncio.run(main())
