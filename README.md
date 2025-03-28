# Introduction

Welcome to the documentation for the XMARTe interface. A Graphical user interface for configuring, simulating and compiling MARTe2 Applications in a graphically based configuration method, mostly known as block based programming.

## Intended Use

It is assumed that users have knowledge of MARTe2 prior to using this application.

The application is intended for end users to develop MARTe2 applications rather than text based config files, this gives the user the ability to define and manage configurations in a graphical user interface.

This application helps generate configuration files for MARTe2, to actually use the files you will need MARTe2 compiled alongside MARTe2-components and setup to be usable - namely with the [traditional marte shell script](https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2-demos-padova/-/blob/master/Startup/Main.sh?ref_type=heads). Initial setup instructions for MARTe2 and it's dependencies can be [found here](https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2-demos-padova/-/tree/master?ref_type=heads).

## Contributing & Support

When you require support please open an issue, if you would like to make adjustments to behaviour, code or additions to features, please do so as an issue and merge request.

**Note: You must comply with our guidelines as per the below.**

[Repository Guidelines](https://github.com/ukaea/xmarte/blob/main/Guidelines.md)

## Installation

This project can work in both Windows and Linux based systems, requiring access right now to our internal gitlab repository - however in future will be available publicly.

``` bash
pip install xmarte
```

## Running

Running the GUI can be done via the command:

``` bash
python -m xmarte
```

For further guidance and documentation on using the GUI please refer to:

<a href="https://ukaea.github.io/xmarte/">Official Documentation</a>

### Compiling and Simulation

To run the compiler or simulator, you can run these locally but need to have installed on Linux docker, on windows you will need to install WSL and then sequently docker on your WSL setup.
If you wish to run the compiler or simulator remotely, you will need to setup a remote server and then configure the server as mentioned in the <a href="https://ukaea.github.io/xmarte/options.html#remote-execution">documentation here</a>.

**Note: By default the system assumes you have selected a local compilation/simulation.**

## Current Features

- Define new and read pre-existing configurations.
- Manage the state machine: states, events and messages.
- Manage a HTTP Instance and messages included.
- Use the standard GAMs and DataSources.*
- Type Database for managing simple, complex and nested types.
- Simulation framework to test configurations.
- Graphing to view recorded data.

## Support

For support on using this application you can refer to the documentation found here:

[User Documentation](https://ukaea.github.io/xmarte/)

If you have found a bug or have a feature request then please submit an issue within this repository.

If you need additional support feel free to contact our team:

- [Edward Jones](mailto:edward.jones1@ukaea.uk)
- [Adam Stephen](mailto:adam.stephen@ukaea.uk)
- [Hudson Baker](mailto:hudson.baker@ukaea.uk)

Additionally you can utilise the MARTe Discord community server:

[MARTe Discord Server](https://discord.gg/anSXWtnprW)

## License

This software repository is provided under the European Union Public Licence as it's rooted in the use of MARTe2. You can find further details on the license [here](https://wayback.archive-it.org/12090/20200210204548/https://ec.europa.eu/idabc/en/document/7774.html).
