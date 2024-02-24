# Changelog

<!--next-version-placeholder-->

## v1.3.0 (2024-02-24)

### Feature

* Add support for platform toolchain file ([`6c4ff60`](https://github.com/cuinixam/yanga/commit/6c4ff60de13a6c5c1f77f77851f879c36f9d750f))

## v1.2.1 (2024-02-24)

### Fix

* Standalone exe causes antivirus false positive ([`d55bfdd`](https://github.com/cuinixam/yanga/commit/d55bfdd6112119ad473131abceb8643871fbb18b))

## v1.2.0 (2024-02-24)

### Feature

* Make variant optional ([`883097c`](https://github.com/cuinixam/yanga/commit/883097cb2e0da0b74bece4cd2ebae8d21655ee04))

## v1.1.0 (2024-02-24)

### Feature

* Print project info when refreshing gui ([`8746958`](https://github.com/cuinixam/yanga/commit/8746958a549d32bdb68e54924e0af0a3e3be1818))

## v1.0.1 (2024-02-24)

### Fix

* Pipeline steps are not loaded in the  exe ([`fd65cd5`](https://github.com/cuinixam/yanga/commit/fd65cd5dd303bc1ee21f013858b4b0c243e60bcf))

## v1.0.0 (2024-02-23)

### Feature

* Replace build command with run ([`0969fb0`](https://github.com/cuinixam/yanga/commit/0969fb0487e61b2f7c378c2bdf2d460008530df1))
* Run single steps and support force run ([`54a3b22`](https://github.com/cuinixam/yanga/commit/54a3b2206dc88006970f678e881f1910d84e5b59))
* Implement run step command ([`1870150`](https://github.com/cuinixam/yanga/commit/187015000e154a061e34de19de3a0e03f5cdeb47))

### Fix

* Coverage job error when using subprocess ([`6087267`](https://github.com/cuinixam/yanga/commit/6087267073df228b603eaa086be93039ccbc84f8))
* Only build executable for tagged commits ([`9f924e9`](https://github.com/cuinixam/yanga/commit/9f924e9fc9e66f7ec52bbe780f188bff6a9929f0))

### Breaking

* replace build command with run ([`0969fb0`](https://github.com/cuinixam/yanga/commit/0969fb0487e61b2f7c378c2bdf2d460008530df1))

## v0.26.0 (2024-02-17)

### Feature

* Add debug options for test executable ([`3a3dea3`](https://github.com/cuinixam/yanga/commit/3a3dea30cc2278db4dcf872fc192cbd7ab0e232a))

### Fix

* Pytest coverage report generation fails ([`ff76f98`](https://github.com/cuinixam/yanga/commit/ff76f98d40c5881ba657b8e2f44b4e2763240448))
* Bootstrap not running when deps changed ([`5b9f022`](https://github.com/cuinixam/yanga/commit/5b9f02274fbfecad8c32de770c78e457d876f241))

## v0.25.0 (2024-02-14)

### Feature

* Add vscode cmake support for mini project ([`0a35dca`](https://github.com/cuinixam/yanga/commit/0a35dca19adc705017379ed5c527e575da15de95))

## v0.24.0 (2024-02-14)

### Feature

* Bootstrap support pip trusted host ([`ab6714c`](https://github.com/cuinixam/yanga/commit/ab6714c50c779aca74128b40aa34a29534631883))

## v0.23.0 (2024-02-14)

### Feature

* Make python scoop install configurable ([`f824587`](https://github.com/cuinixam/yanga/commit/f82458776851d44724f8887398b692e5a28942f6))

## v0.22.0 (2024-02-13)

### Feature

* Add icon to windows executable ([`ad6c8ab`](https://github.com/cuinixam/yanga/commit/ad6c8abd0bc1a588b9c7b21d0b1edb02886b557f))

## v0.21.7 (2024-02-13)

### Fix

* Release windows executable requires a tag ([`5cbc3f2`](https://github.com/cuinixam/yanga/commit/5cbc3f23aa47e46ae6eaf5e12dc5574926f5f837))

## v0.21.6 (2024-02-13)

### Fix

* Release windows executable requires a tag name ([`889d70f`](https://github.com/cuinixam/yanga/commit/889d70fc470a0c74c6b305959ba74876842479d2))

## v0.21.5 (2024-02-13)

### Fix

* Windows executable still not released ([`cde9cf2`](https://github.com/cuinixam/yanga/commit/cde9cf286d35f11c850b69573b110de33e5ce9df))

## v0.21.4 (2024-02-13)

### Fix

* Windows executable release is not triggered ([`97be7dd`](https://github.com/cuinixam/yanga/commit/97be7dd18feb626c1d1e4bbd26ea59166e10ea61))

## v0.21.3 (2024-02-13)

### Fix

* Windows executable name does not contain tag ([`96ef7e1`](https://github.com/cuinixam/yanga/commit/96ef7e119f5a7fad0bbc10920ca50d60fd44013c))

## v0.21.2 (2024-02-13)

### Fix

* Windows executable is not released ([`1b3122e`](https://github.com/cuinixam/yanga/commit/1b3122ef5975f5a1f39c9ed019d400b286402804))

## v0.21.1 (2024-02-11)

### Fix

* Pyinstaller build github action failed ([`2e4e6d5`](https://github.com/cuinixam/yanga/commit/2e4e6d51930d793ea7cec4beae4ba8e6760255ff))

## v0.21.0 (2024-02-11)

### Feature

* Create windows executable ([`1ac3625`](https://github.com/cuinixam/yanga/commit/1ac36257b7d578e98b60e4d719f7e9b90ce1b027))

## v0.20.0 (2024-01-31)

### Feature

* Bootstrap creates pip.ini for pypi source ([`d4b54e7`](https://github.com/cuinixam/yanga/commit/d4b54e79e63fb01106e07b7067cc6c9bd53d9320))

## v0.19.0 (2024-01-31)

### Feature

* Read bootstrap config from json ([`ed6b688`](https://github.com/cuinixam/yanga/commit/ed6b688f78d8febc0e35e7c0cb0fd97246b44bf0))

### Fix

* Some bootsrap dependencies are missing ([`37aa08b`](https://github.com/cuinixam/yanga/commit/37aa08b9884c45641beacce7bc8c934d30055132))

## v0.18.1 (2024-01-22)

### Fix

* Py-app-dev version is not compatible ([`1d52931`](https://github.com/cuinixam/yanga/commit/1d52931d039bd1c435b901f6ba588e62b24909f1))

## v0.18.0 (2024-01-10)

### Feature

* Add support for loading installed stages ([`d2a941e`](https://github.com/cuinixam/yanga/commit/d2a941e83f322f4782cc6b7922222ace558e55f2))

## v0.17.1 (2024-01-10)

### Fix

* Gui command help message is incorrect ([`91b7784`](https://github.com/cuinixam/yanga/commit/91b778418a6c07da1c36af1f596a760d0d836575))

## v0.17.0 (2023-12-22)

### Feature

* Make mini project default for init ([`982f494`](https://github.com/cuinixam/yanga/commit/982f494afbc3702b55d69ceadb2d0d73ef3fd523))
* Add custom build request for cli ([`1316177`](https://github.com/cuinixam/yanga/commit/1316177a410dda603e6ace655ee9d6a471ab172e))
* Add variant selection in command line ([`c117cfa`](https://github.com/cuinixam/yanga/commit/c117cfa4fc16916af8ebdb6d6c8df8dedba07301))

## v0.16.0 (2023-12-17)

### Feature

* Add gtest example to mini project ([`ad4c622`](https://github.com/cuinixam/yanga/commit/ad4c62253782acdb148c84b015618453adb31ef0))

## v0.15.0 (2023-12-17)

### Feature

* Integrate unit testing with gtest ([`caa9300`](https://github.com/cuinixam/yanga/commit/caa9300aa9f85231fcff0a2414374f375de2130b))

## v0.14.0 (2023-12-09)

### Feature

* Add open in vscode button ([`16b4228`](https://github.com/cuinixam/yanga/commit/16b422855dcfa82a0069920f00999f509e21920e))
* Install gtest with west ([`c8e31fc`](https://github.com/cuinixam/yanga/commit/c8e31fc18c2d0f5f4799f74b53ae63d8ff7874fa))

### Fix

* Missing abstract method decorator ([`272a4cd`](https://github.com/cuinixam/yanga/commit/272a4cd667c763a08312b06a0c43e277631d5a58))

## v0.13.0 (2023-12-03)

### Feature

* Implement component compile target ([`4336fcb`](https://github.com/cuinixam/yanga/commit/4336fcbaa3be1f5fe93f2c023d40ca6af6b41046))

## v0.12.0 (2023-11-26)

### Feature

* Propagate install dirs in the environment ([`f814a0f`](https://github.com/cuinixam/yanga/commit/f814a0f664939d1c65caa78ea681cca69c827f46))
* Exclude directories from config search ([`44abdae`](https://github.com/cuinixam/yanga/commit/44abdaebcae6490f687ef656e8b0c040e2be2db6))
* Integrate KConfig generation ([`1f0bc8e`](https://github.com/cuinixam/yanga/commit/1f0bc8e54938f6a03506268dc0633808cfa8ffbf))

## v0.11.1 (2023-11-02)

### Fix

* Bootstrap automatically calls yanga ([`3168a58`](https://github.com/cuinixam/yanga/commit/3168a58fb4ce5dd1d8fdb96614a756dce18ec5f7))
* Scoop installer prompts to open tmp file ([`c4bfab3`](https://github.com/cuinixam/yanga/commit/c4bfab3cda594b163868034816cc8924f025f8dd))

## v0.11.0 (2023-11-02)

### Feature

* Add option to init bootstrap files ([`9d8fc84`](https://github.com/cuinixam/yanga/commit/9d8fc84b24f878ef3f7932517e8db52fdaace248))

### Fix

* Gui icons dependencies missing ([`be38650`](https://github.com/cuinixam/yanga/commit/be38650b570258381f7d7a3030bd2fa3533a679c))

## v0.10.0 (2023-10-25)

### Feature

* Gui handle user exception during build ([`5e17d52`](https://github.com/cuinixam/yanga/commit/5e17d52dbb2c191305f7665cf015697270828fbf))

### Fix

* Print subprocess output in realtime ([`10cf353`](https://github.com/cuinixam/yanga/commit/10cf353265413db08176ae228fcae9a3cfa57f34))
* Yanga build only depends on configure ([`a91f18c`](https://github.com/cuinixam/yanga/commit/a91f18cd52a41e03f60f968a7b93d62712a8dec5))

## v0.9.0 (2023-10-23)

### Feature

* Create template for minimal yanga project ([`84b3ff6`](https://github.com/cuinixam/yanga/commit/84b3ff61264fbd49f1250514fe806479f81c6530))
* Add cmake build stage ([`0615305`](https://github.com/cuinixam/yanga/commit/06153051c6e0905efb63ea84ff48b5447553360d))
* Add build configure stage ([`9463a2c`](https://github.com/cuinixam/yanga/commit/9463a2cf69fb956bb511908cfe013d95e2d22fda))

### Fix

* Integration tests for python 3.10 ([`8cbe239`](https://github.com/cuinixam/yanga/commit/8cbe2397c827f3971a4173bbf987f073c0ef8826))
* Build stage fails while writing file ([`344a4ad`](https://github.com/cuinixam/yanga/commit/344a4adc37372106b9b035d65a36659091c5a6b3))
* Variant bom components are ignored ([`2c38f52`](https://github.com/cuinixam/yanga/commit/2c38f52a9068f5818b956f16312b8d96a40a9a58))

## v0.8.2 (2023-10-21)

### Fix

* Project root user config not found ([`a088190`](https://github.com/cuinixam/yanga/commit/a088190f915d956b34d15f52c20566a49805771b))

### Documentation

* Clean up ([`6a82bab`](https://github.com/cuinixam/yanga/commit/6a82babe51d8036f1d06900d31cf3b5e90bfda58))
* Use dark mode ([`8386089`](https://github.com/cuinixam/yanga/commit/8386089f3cb788753d0759d7a503e6550227b6b2))

## v0.8.1 (2023-09-30)

### Fix

* Scoop install not run if tool is uninstalled ([`5547b88`](https://github.com/cuinixam/yanga/commit/5547b88519b300073eb33720aede0d4c128adcf1))

## v0.8.0 (2023-09-29)

### Feature

* Add dummy yanga build stage ([`e65a7cb`](https://github.com/cuinixam/yanga/commit/e65a7cb4d7ed67a3c6fd9e145b022b81c2afe59d))

## v0.7.0 (2023-07-09)

### Feature

* Automatically build yanga projects ([`3101666`](https://github.com/cuinixam/yanga/commit/31016662f543a00198184818e700fb70261d1739))

## v0.6.0 (2023-07-09)

### Feature

* Update bootstrap to only run if required ([`55f1c8f`](https://github.com/cuinixam/yanga/commit/55f1c8fe60933be86c053ea7370d9ae2074a84fd))
* Update pipeline to use the executor ([`eb3f676`](https://github.com/cuinixam/yanga/commit/eb3f676ac83d7a2ec0f8e8d6be78127ae4fef6c7))
* Implement runnable executor ([`7462d63`](https://github.com/cuinixam/yanga/commit/7462d63e15f016c1d8967c9c42f311247945e3a7))
* Support build.py for linux ([`26b0542`](https://github.com/cuinixam/yanga/commit/26b05428e870b6d0504933f4877ed0e854542f18))

### Fix

* Bootstrap for Unix fails running commands ([`8085a05`](https://github.com/cuinixam/yanga/commit/8085a05d8d57cf1de538105f5b31a7dd565c2c73))

## v0.5.0 (2023-07-05)

### Feature

* Support user pipeline stages ([`4cd2d2c`](https://github.com/cuinixam/yanga/commit/4cd2d2c61e992252befc523508efe6a2c0e4b3cd))

## v0.4.0 (2023-07-05)

### Feature

* Add --version option ([`4b1eeee`](https://github.com/cuinixam/yanga/commit/4b1eeee37168b47037c08aa48a2b24e45da2f5d6))
* Add install command for scoop ([`045b767`](https://github.com/cuinixam/yanga/commit/045b767e7c4e258e8bf21947510f05841bb4dcc3))

## v0.3.0 (2023-07-03)

### Feature

* Scoop apps installer wrapper ([`2221c36`](https://github.com/cuinixam/yanga/commit/2221c360dd129102678173e108befedb0bfde9fc))

## v0.2.3 (2023-07-03)

### Fix

* Init command fails because dir exists ([`93ddefb`](https://github.com/cuinixam/yanga/commit/93ddefb398a4d4cef6b83c6ac68ac923e2d5f221))

## v0.2.2 (2023-07-03)

### Fix

* Init command fails because dir is not empty ([`fb57839`](https://github.com/cuinixam/yanga/commit/fb57839d5a2c60e4a87305f408012aaba1d6b3ae))

### Documentation

* Collect some ideas to implement next ([`be266b0`](https://github.com/cuinixam/yanga/commit/be266b07e309a12e9a0da1dce13f4856310e8aa3))

## v0.2.1 (2023-07-02)

### Fix

* Python fails because of missing bucket ([`924dcb1`](https://github.com/cuinixam/yanga/commit/924dcb11e53e354501832a3bc809a1fe2fcc8a52))

## v0.2.0 (2023-07-02)

### Feature

* Update bootstrap script ([`e06745b`](https://github.com/cuinixam/yanga/commit/e06745bf45a93ce5cad1c18b98c0a9043f5f1b73))
* Support for python 3.10 ([`ea18623`](https://github.com/cuinixam/yanga/commit/ea18623c50c7fd35fd576dd6577de49a63a79900))
* Support windows and python >=3.11 ([`1cee197`](https://github.com/cuinixam/yanga/commit/1cee197ce69652c065af99b084e6648125c2d7a5))
* Collect installed scoop apps ([`f90e73a`](https://github.com/cuinixam/yanga/commit/f90e73ab142ecac9b8ce1aa1a20601cce89bef5f))
* Build script installs python dependencies ([`fa94d4e`](https://github.com/cuinixam/yanga/commit/fa94d4e4c02892241aedc08ff1fe3b3c75f134ee))
* Add init command with only build scripts ([`7f4a145`](https://github.com/cuinixam/yanga/commit/7f4a145538376bc44e4b397df480c2f8983cbaad))

### Fix

* Build.py test wrongly installs poetry deps ([`61fe118`](https://github.com/cuinixam/yanga/commit/61fe1180548ff89a751e0fcd493f9505619f27e1))

## v0.1.0 (2023-06-06)
### Feature
* Add command line parser ([`7a6c1bd`](https://github.com/cuinixam/yanga/commit/7a6c1bd696f03c02ed0686b45ad6000ead827c1a))
* Add variant configuration ([`d0a823c`](https://github.com/cuinixam/yanga/commit/d0a823c27d18582f407f4c18832c17123edfb3a7))
* Add logger based on loguru ([`251ffb3`](https://github.com/cuinixam/yanga/commit/251ffb3c6e51dc0b6288804253bb03e446c2335e))

### Fix
* Readthedocs build is failing ([`8b55345`](https://github.com/cuinixam/yanga/commit/8b55345ea79e1336a80296330828cf7b53dcb25b))

### Documentation
* Add requirements tests traceability ([`6fe3d22`](https://github.com/cuinixam/yanga/commit/6fe3d2208105b1084ae725eabd8812b5883499af))
* Brainstorming artifacts ([`5ccd062`](https://github.com/cuinixam/yanga/commit/5ccd06265e4c550e94219ef1794bff9eb2b8fc92))
