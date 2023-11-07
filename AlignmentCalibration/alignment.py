import ROOT
import math
import array

class TRIANGLE_FUNCTION:
    def __call__(self, u, par):
        height, shift = par[0], par[1]
        x = u[0]
        x -= shift 
        if abs(x) > 17.0:
            return 0.0
        else: 
            return height * (17.0 - abs(x))
trianglefunction = TRIANGLE_FUNCTION()

def MyFit(h2BaseLpos, h1BaseReturn, ModTitle, i=-1):
    c2 = ROOT.TCanvas("dummy", "dummy")
    c2.cd()

    NumberLposBins = h2BaseLpos.GetYaxis().GetNbins()
    NumberRotationPoints = 6
    NumberRotationBins = NumberLposBins // NumberRotationPoints

    H1Name = ""
    F1Name = ""
    if i >= 0 and i < NumberRotationPoints:
        H1Name = '{}_rot{}'.format(ModTitle, i)
        F1Name = '{}_fit_rot{}'.format(ModTitle, i)
        minbin = i * NumberRotationBins
        maxbin = minbin + NumberRotationBins
        h1Base = h2BaseLpos.ProjectionX(H1Name, minbin, maxbin)
    else:
        H1Name = '{}_shift'.format(ModTitle)
        F1Name = '{}_fit'.format(ModTitle)
        h1Base = h2BaseLpos.ProjectionX(H1Name)

    h1Base.Scale(1.0 / NumberLposBins)
    h1Base.SetName(H1Name)
    h1Base.SetTitle(H1Name)
    h1Base.GetYaxis().SetTitle("Energy (MeV)")

    f1 = ROOT.TF1(F1Name, trianglefunction, -17.0, +17.0, 2)
    f1.SetParameter(0, 3.5)
    f1.SetParameter(1, 0.0)
    
    h1Base.Fit(F1Name, "Q", "Q")
    shift = f1.GetParameter(1)
    h1Base.Fit(F1Name, "Q", "Q", shift - 10.0, shift + 10.0)
    shift = f1.GetParameter(1)

    if h1BaseReturn != 0:
        h1BaseReturn = h1Base

    return shift

def DoAlignment():
    fptext = open("AlignmentConstants.txt", "w")

    fin = ROOT.TFile("ReadNT.root")
    moduleLposBase = fin.Get("moduleLposBase")
    
    moduleLposBase.GetYaxis().SetTitle("lpos")
    moduleLposBase.GetZaxis().SetTitle("triangle base")
    
    c1 = ROOT.TCanvas("c1", "c1")
    c1.Divide(2, 2)
    c1.Print("AlignmentBook.pdf[")

    for modbin in range(1, 241):
        module_number = moduleLposBase.GetXaxis().GetBinLowEdge(modbin)
        module = int(5 + module_number) - 5
        plane = int(2 * (module_number + 5)) % 2 + 1

        print("Doing alignment for module", module, "plane", plane)

        if plane == 1:
            c1.Clear("D")

        ModTitle = ""
        if module >= 0:
            ModTitle = "mod{:03d}pl{:1d}".format(module, plane)
        if module < 0:
            ModTitle = "modm{:1d}pl{:1d}".format(module, plane)

        moduleLposBase.GetXaxis().SetRange(modbin, modbin)

        H2Name = "{}_2D".format(ModTitle)
        h2BaseLpos = moduleLposBase.Project3D("yz")
        h2BaseLpos.SetName(H2Name)
        h2BaseLpos.SetTitle("Module {} Plane {};Base Position (mm);Longitudinal Position (mm);Average Energy (MeV)".format(module, plane))

        if h2BaseLpos.GetEntries() == 0:
            continue

        h1Base = ROOT.TH1D()
        shift = -MyFit(h2BaseLpos, h1Base, ModTitle)

        lpos_point = array.array('d', [-1200.0 + 400.0 * i + 200.0 for i in range(6)])
        shift_point = array.array('d', [MyFit(h2BaseLpos, 0, ModTitle, i) for i in range(6)])
        
        tgrRotation = ROOT.TGraph(6, shift_point, lpos_point)
        tgrFit = ROOT.TGraph(6, lpos_point, shift_point)
        tgrFit.Fit("pol1", "Q", "Q")
        LowPoint = tgrFit.GetFunction("pol1").Eval(-1000.0)
        HighPoint = tgrFit.GetFunction("pol1").Eval(1000.0)
        rotation = 1000 * math.atan((HighPoint - LowPoint) / 2000.0)

        c1.cd(2 * (plane - 1) + 1)
        h2BaseLpos.SetMaximum(4)
        h2BaseLpos.Draw("colz")
        tgrRotation.SetMarkerStyle(ROOT.kOpenCircle)
        tgrRotation.Draw("P same")
        tline = ROOT.TLine(LowPoint, -1000.0, HighPoint, 1000.0)
        tline.SetLineWidth(3)
        tline.Draw("same")
        c1.cd(2 * (plane - 1) + 2)
        h1Base.SetMaximum(4)
        h1Base.SetTitle("Module {} Plane {};Base Position (mm);Average Energy (MeV)".format(module, plane))
        h1Base.Draw()
        ModString = "Module {} Plane {}".format(module, plane)
        ShiftString = "Shift = {:+5.3f} mm".format(shift)
        RotationString = "Rotation = {:+5.3f} mrad\n".format(rotation)
        ModLabel = ROOT.TPaveLabel(5.0, 4.00, 17.0, 3.75, ModString)
        ShiftLabel = ROOT.TPaveLabel(5.0, 3.75, 17.0, 3.50, ShiftString)
        RotationLabel = ROOT.TPaveLabel(5.0, 3.50, 17.0, 3.25, RotationString)
        ModLabel.Draw()
        ShiftLabel.Draw()
        RotationLabel.Draw()
        if plane == 2:
            c1.Print("AlignmentBook.pdf")

        c2 = ROOT.TCanvas("c2", "c2", 800, 500)
        c2.Divide(2, 1)
        c2.cd(1)
        h1Base.Draw()
        c2.cd(2)
        h2BaseLpos.Draw("colz")
        tgrRotation.Draw("P same")
        tline.Draw("same")
        if plane == 2:
            c1.Print("AlignmentBook.pdf")
        c2.Print("alignmentPlotDump/mod{:03d}pl{}.png".format(module, plane))
        del c2

        fptext.write("module: {} plane: {} shift: {} rotation: {}\n".format(module, plane, shift, rotation))
    c1.
    c1.Print("AlignmentBook.pdf]")
    fptext.close()

DoAlignment()