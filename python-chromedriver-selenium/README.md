# python-chromedriver-selenium

This is generalized container meant to support Selenium Python bindings and Chromedriver.

## Quick Try

```shell
$ docker run -it hub.opensciencegrid.org/slate/python-chromedriver-selenium:3.9-debian sh
/opt/project # 
```

## Image Includes

* Python (Debian-based)
* Google Chrome
* Chromedriver
* Selenium
* Docker environmental variables:
  * `SCREENSHOTS`
    * Default value is `1`
    * Example usage in `main.py`:
      ```python
      if os.environ.get('SCREENSHOTS') == 1:
        self.driver.save_screenshot('/opt/project/hello-world.png')
      ```

## Examples

### Run Selenium test in the container

1. Change to a directory containing Selenium tests.
1. Run `main.py` in the container:
   ```shell
   docker run -it -v $PWD:/opt/project hub.opensciencegrid.org/slate/python-chromedriver-selenium:3.9-alpine python main.py
   ```

### Run Selenium test in GitHub action

TBD

## References

* [DockerHub: joyzoursky/python-chromedriver](https://hub.docker.com/r/joyzoursky/python-chromedriver)
