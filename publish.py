import sys, getpass, package, ftplib, time, os

def publish(platform, tag, srcFile, password):
    cdnURL   = "ftp.boman.io"
    username = "donalonzo"
    libRoot  = "/res/{0}/{1}".format(platform, tag)
    fileName = "lib-{0}-{1}.zip".format(platform, tag)
    date     = "{}-{}".format(time.strftime("%Y-%m-%d"), int(time.time()))

    try:
        session = ftplib.FTP(cdnURL, username, password)
        if not tag in session.nlst("/res/{0}".format(platform)):
            raise Exception("This configuration has not been setup yet.")

        # Release as archived and latest
        for path in [date, "latest"]:
            # Change directory (Create if it does not exist)
            dir = "{}/{}".format(libRoot, path)
            if not path in session.nlst(libRoot):
                session.mkd(dir)
            session.cwd(dir)

            # Upload file
            with open(srcFile, "rb") as file:
                session.storbinary("STOR {}".format(fileName), file)
    except ftplib.all_errors as e:
        print (str(e))