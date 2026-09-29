package com.hms.controller;

import java.io.IOException;
import java.sql.Date;
import java.util.List;

import com.hms.dao.BillingDAO;
import com.hms.model.Bill;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet("/BillingServlet")
public class BillingServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private BillingDAO billingDAO;

    @Override
    public void init() throws ServletException {
        billingDAO = new BillingDAO();
    }

    // =========================
    // GET REQUESTS
    // =========================

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        if (action == null || "list".equals(action)) {

            listBills(request, response);

        } else if ("search".equals(action)) {

            searchBills(request, response);

        } else if ("edit".equals(action)) {

            editBill(request, response);

        } else if ("delete".equals(action)) {

            deleteBill(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/BillingServlet?action=list"
            );
        }
    }


    // =========================
    // POST REQUESTS
    // =========================

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        if ("add".equals(action)) {

            addBill(request, response);

        } else if ("update".equals(action)) {

            updateBill(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/BillingServlet?action=list"
            );
        }
    }


    // =========================
    // LIST BILLS
    // =========================

    private void listBills(HttpServletRequest request,
                           HttpServletResponse response)
            throws ServletException, IOException {

        List<Bill> bills = billingDAO.getAllBills();

        request.setAttribute("bills", bills);

        request.getRequestDispatcher("/billing.jsp")
               .forward(request, response);
    }


    // =========================
    // ADD BILL
    // =========================

    private void addBill(HttpServletRequest request,
                         HttpServletResponse response)
            throws IOException {

        try {

            int patientId =
                Integer.parseInt(request.getParameter("patientId"));

            String appointmentText =
                request.getParameter("appointmentId");

            int appointmentId = 0;

            if (appointmentText != null
                    && !appointmentText.trim().isEmpty()) {

                appointmentId =
                    Integer.parseInt(appointmentText);
            }

            double amount =
                Double.parseDouble(request.getParameter("amount"));

            String paymentMethod =
                request.getParameter("paymentMethod");

            String paymentStatus =
                request.getParameter("paymentStatus");

            String billDateText =
                request.getParameter("billDate");

            Date billDate =
                Date.valueOf(billDateText);


            // Validation

            if (patientId <= 0
                    || amount < 0
                    || billDateText == null
                    || billDateText.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-bill.jsp?error=invalid"
                );

                return;
            }


            if (paymentStatus == null
                    || paymentStatus.trim().isEmpty()) {

                paymentStatus = "Pending";
            }


            Bill bill = new Bill();

            bill.setPatientId(patientId);
            bill.setAppointmentId(appointmentId);
            bill.setAmount(amount);
            bill.setPaymentMethod(paymentMethod);
            bill.setPaymentStatus(paymentStatus);
            bill.setBillDate(billDate);


            boolean success =
                billingDAO.addBill(bill);


            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-bill.jsp?error=failed"
                );
            }


        } catch (IllegalArgumentException e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-bill.jsp?error=invalid"
            );

        } catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-bill.jsp?error=failed"
            );
        }
    }


    // =========================
    // EDIT BILL
    // =========================

    private void editBill(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        try {

            int id =
                Integer.parseInt(request.getParameter("id"));

            Bill bill =
                billingDAO.getBillById(id);


            if (bill == null) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=list"
                );

                return;
            }


            request.setAttribute("bill", bill);

            request.getRequestDispatcher(
                    "/edit-bill.jsp")
                   .forward(request, response);


        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/BillingServlet?action=list"
            );
        }
    }


    // =========================
    // UPDATE BILL
    // =========================

    private void updateBill(HttpServletRequest request,
                            HttpServletResponse response)
            throws IOException {

        int id = 0;

        try {

            id =
                Integer.parseInt(request.getParameter("id"));

            int patientId =
                Integer.parseInt(request.getParameter("patientId"));

            String appointmentText =
                request.getParameter("appointmentId");

            int appointmentId = 0;

            if (appointmentText != null
                    && !appointmentText.trim().isEmpty()) {

                appointmentId =
                    Integer.parseInt(appointmentText);
            }

            double amount =
                Double.parseDouble(request.getParameter("amount"));

            String paymentMethod =
                request.getParameter("paymentMethod");

            String paymentStatus =
                request.getParameter("paymentStatus");

            Date billDate =
                Date.valueOf(
                    request.getParameter("billDate")
                );


            if (id <= 0
                    || patientId <= 0
                    || amount < 0) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/edit-bill.jsp?id="
                    + id
                    + "&error=invalid"
                );

                return;
            }


            if (paymentStatus == null
                    || paymentStatus.trim().isEmpty()) {

                paymentStatus = "Pending";
            }


            Bill bill = new Bill();

            bill.setId(id);
            bill.setPatientId(patientId);
            bill.setAppointmentId(appointmentId);
            bill.setAmount(amount);
            bill.setPaymentMethod(paymentMethod);
            bill.setPaymentStatus(paymentStatus);
            bill.setBillDate(billDate);


            boolean success =
                billingDAO.updateBill(bill);


            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=edit&id="
                    + id
                    + "&error=failed"
                );
            }


        } catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/BillingServlet?action=edit&id="
                + id
                + "&error=invalid"
            );
        }
    }


    // =========================
    // DELETE BILL
    // =========================

    private void deleteBill(HttpServletRequest request,
                            HttpServletResponse response)
            throws IOException {

        try {

            int id =
                Integer.parseInt(request.getParameter("id"));

            boolean success =
                billingDAO.deleteBill(id);


            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/BillingServlet?action=list&error=delete"
                );
            }


        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/BillingServlet?action=list"
            );
        }
    }


    // =========================
    // SEARCH BILLS
    // =========================

    private void searchBills(HttpServletRequest request,
                             HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
            request.getParameter("keyword");

        if (keyword == null) {
            keyword = "";
        }


        List<Bill> bills =
            billingDAO.searchBills(keyword);


        request.setAttribute("bills", bills);

        request.setAttribute(
            "searchKeyword",
            keyword
        );


        request.getRequestDispatcher(
                "/billing.jsp")
               .forward(request, response);
    }
}