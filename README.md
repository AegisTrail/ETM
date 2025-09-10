**ETM (Ethereum Telegram Machine) Wallet: A Telegram based Ethereum Bot for Testing**

This project is a Telegram bot designed for interacting with the Ethereum blockchain.

It is built using **[web3.py](https://web3py.readthedocs.io/)** for Ethereum interactions and **[python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/)** for Telegram integration.

By default, it uses **[Anvil](https://getfoundry.sh/anvil/reference/)** for rapid prototyping and deployment. (You won't end up losing coins because you are rich at the start of every anvil)

<p align="center">
    <img src="https://i.imgflip.com/a5ok4y.jpg" alt="Image" width="300"/>
</p>


> [!CAUTION] 
> This project is **not audited for security** and is intended solely for a controlled development environment.  
Using it on mainnet or with any real assets is **strongly discouraged**.

#### Features:

The bot provides a simple interface for common Ethereum and token-related commands directly within Telegram.

#### Commands:

-   **/start**: Display the welcome message and command list.
    
-   **/new**: Register a new derived wallet index.
    
-   **/address**: Show your derived wallet address.
    
-   **/balance [address]**: Show the ETH balance for a given address.
    
-   **/send**: Initiate a guided process to send ETH.
    
-   **/history [blocks]**: Scan the last _n_ blocks for transactions.
    
-   **/sign**: Sign a message with your wallet.
    
-   **/verify**: Verify a signed message (requires address, message, and signature).
    
-   **/faucet [amount]**: Request a specific amount of ETH from the development faucet (developer use only).
    
-   **/token_add [decimals]**: Add a new token to your tracked list.
    
-   **/token_balance** : Check the balance of a tracked token.
    
-   **/token_send**: Initiate a guided process to send a tracked token.


#### Setup:

#### Prerequisites

-   You must have **Python** and **uv** installed to manage dependencies and run the project.
    

#### Using UV

1.  Synchronize/Install dependencies:
    
    ```bash
    uv sync
    ```
    
2.  Rename `.env.example` file to `.env` and configure environment variables.

3. Make sure your Anvil RPC server is running! 
      ```bash
        anvil
    ``` 
    
4.  Run the bot:
    
    ```bash
    uv run run.py
    ```
    

#### Using Docker / Podman

Alternatively, you can use Docker to get the bot running quickly.

1. Configure environment variables in `.env` 

2. Build and run the container:

   ```bash
    docker compose up
    ```

-----

#### Contributing:
PRs, forking, and playing with the code are welcomed! Feel free to contribute to the project.

#### LICENSE :
This project is licensed under the GNU General Public License (GPL) v3

![GNU General Public License](https://www.gnu.org/graphics/gplv3-with-text-136x68.png)

