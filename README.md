<img src="https://img.shields.io/github/issues/WikiMovimentoBrasil/wlb?style=for-the-badge"/> <img src="https://img.shields.io/github/license/WikiMovimentoBrasil/wlb?style=for-the-badge"/> <img src="https://img.shields.io/github/languages/top/WikiMovimentoBrasil/wlb?style=for-the-badge"/>
# Wiki Loves Bahia

This app allows users to register to the Wiki Loves Bahia photographic contest. It requires the user to choose one educational institution ad the one they are a part of. This data is solely used to compile the information of each institution for the awards to be distributed later on. The data is encrypted and anonymized in a way that cannot be retraced to the user's Wiki account.

This tool is available live at: https://wlb.toolforge.org/

## Installation

There are several packages need to this application to function. All of them are listed in the <code>requirements.txt</code> file. To install them, use

```bash
pip install -r requirements.txt
```

You also need to set the configuration file. To do this, you need [a Oauth consumer token and Oauth consumer secret](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose).
Your config file should look like this:
```bash
ENCRYPTION_KEY: "ENCRYPTION_KEY"
SECRET_KEY: "SECRET_KEY"
APPLICATION_ROOT: "wlb/"
OAUTH_MWURI: "https://meta.wikimedia.org/w/index.php"
CONSUMER_KEY: "CONSUMER_KEY"
CONSUMER_SECRET: "CONSUMER_SECRET"
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GNU General Public License v3.0](https://github.com/WikiMovimentoBrasil/wikimarcas/blob/master/LICENSE)

## Credits
This application was developed by the Wiki Movimento Brasil User Group.